import datetime
import json
from types import SimpleNamespace

import pytest
from telethon.tl import functions, types

from telegram_mcp.tools import messages


UTC = datetime.timezone.utc


class FakeClient:
    def __init__(self, items, own_user_id=31848766):
        self.items = {item.id: item for item in items}
        self.own_user_id = own_user_id
        self.requests = []

    async def get_me(self):
        return SimpleNamespace(id=self.own_user_id)

    async def iter_messages(self, entity, from_user=None):
        for item in sorted(self.items.values(), key=lambda item: item.id, reverse=True):
            yield item

    async def get_messages(self, entity, ids):
        return [self.items.get(message_id) for message_id in ids]

    async def __call__(self, request):
        self.requests.append(request)
        for message_id in request.id:
            self.items.pop(message_id, None)
        return SimpleNamespace(pts_count=len(request.id))


def _message(message_id, sender_id, day):
    return SimpleNamespace(
        id=message_id,
        sender_id=sender_id,
        date=datetime.datetime(2026, 8, day, tzinfo=UTC),
    )


@pytest.fixture(autouse=True)
def clear_previews():
    messages._delete_own_previews.clear()


def _patch(monkeypatch, client):
    entity = SimpleNamespace(title="Mindist Syndicate")

    async def resolve_entity(chat_id, cl):
        return entity

    async def ensure_connected(cl):
        return None

    monkeypatch.setattr(messages, "get_client", lambda account=None: client)
    monkeypatch.setattr(messages, "resolve_entity", resolve_entity)
    monkeypatch.setattr(messages, "ensure_connected", ensure_connected)
    monkeypatch.setattr(messages, "_is_group_entity", lambda candidate: candidate is entity)
    monkeypatch.setattr(messages, "get_marked_id", lambda candidate: -123456)
    monkeypatch.setattr(messages.secrets, "token_urlsafe", lambda size: "test-token")
    return entity


async def _preview(monkeypatch, client):
    _patch(monkeypatch, client)
    payload = json.loads(await messages.preview_delete_own_messages(chat_id=-123456))
    return payload


@pytest.mark.asyncio
async def test_preview_selects_only_current_accounts_messages(monkeypatch):
    client = FakeClient(
        [
            _message(30, 31848766, 3),
            _message(20, 999, 2),
            _message(10, 31848766, 1),
        ]
    )

    payload = await _preview(monkeypatch, client)

    assert payload["status"] == "confirmation_required"
    assert payload["chat_title"] == "Mindist Syndicate"
    assert payload["message_count"] == 2
    assert payload["newest_message_ids"] == [30, 10]
    assert "DELETE FOR EVERYONE" in payload["confirmation_phrase"]
    assert "own_messages=2" in payload["confirmation_phrase"]
    assert client.requests == []


@pytest.mark.asyncio
async def test_delete_refuses_wrong_confirmation_without_api_call(monkeypatch):
    client = FakeClient([_message(10, 31848766, 1)])
    payload = await _preview(monkeypatch, client)

    result = await messages.delete_own_messages_for_everyone(
        chat_id=-123456,
        preview_token=payload["preview_token"],
        confirmation_phrase="yes",
    )

    assert result == "Refused: confirmation phrase does not exactly match the preview."
    assert client.requests == []
    assert 10 in client.items


@pytest.mark.asyncio
async def test_delete_uses_revoke_true_and_never_deletes_other_sender(monkeypatch):
    client = FakeClient(
        [
            _message(30, 31848766, 3),
            _message(20, 999, 2),
            _message(10, 31848766, 1),
        ]
    )
    payload = await _preview(monkeypatch, client)

    result = json.loads(
        await messages.delete_own_messages_for_everyone(
            chat_id=-123456,
            preview_token=payload["preview_token"],
            confirmation_phrase=payload["confirmation_phrase"],
        )
    )

    assert result["status"] == "complete"
    assert result["confirmed_messages_deleted"] == 2
    assert result["revoke_requested"] is True
    assert result["confirmed_ids_absent_after_delete"] is True
    assert set(client.items) == {20}
    assert len(client.requests) == 1
    request = client.requests[0]
    assert isinstance(request, functions.messages.DeleteMessagesRequest)
    assert request.revoke is True
    assert set(request.id) == {10, 30}


@pytest.mark.asyncio
async def test_delete_refuses_snapshot_drift_before_first_api_call(monkeypatch):
    client = FakeClient([_message(10, 31848766, 1)])
    payload = await _preview(monkeypatch, client)
    client.items[11] = _message(11, 31848766, 2)

    result = await messages.delete_own_messages_for_everyone(
        chat_id=-123456,
        preview_token=payload["preview_token"],
        confirmation_phrase=payload["confirmation_phrase"],
    )

    assert "set of your messages changed" in result
    assert client.requests == []
    assert set(client.items) == {10, 11}


@pytest.mark.asyncio
async def test_supergroup_delete_uses_server_wide_channel_request(monkeypatch):
    client = FakeClient([_message(10, 31848766, 1)])
    entity = types.Channel(
        id=123456,
        title="Mindist Syndicate",
        photo=types.ChatPhotoEmpty(),
        date=datetime.datetime(2026, 8, 1, tzinfo=UTC),
        creator=False,
        left=False,
        broadcast=False,
        verified=False,
        megagroup=True,
        restricted=False,
        signatures=False,
        min=False,
        scam=False,
        has_link=False,
        has_geo=False,
        slowmode_enabled=False,
        call_active=False,
        call_not_empty=False,
        fake=False,
        gigagroup=False,
        noforwards=False,
        join_to_send=False,
        join_request=False,
        forum=False,
        stories_hidden=False,
        stories_hidden_min=False,
        stories_unavailable=False,
        access_hash=789,
    )

    await messages._delete_message_ids_for_everyone(client, entity, [10])

    assert isinstance(client.requests[0], functions.channels.DeleteMessagesRequest)
    assert client.requests[0].id == [10]
