import datetime
import json

import pytest
from telethon.tl import types

from telegram_mcp.tools import groups


UTC = datetime.timezone.utc
ME_ID = 31848766
TARGET_ID = 50038113
CHAT_ID = -1001680450875


def _supergroup():
    return types.Channel(
        id=1680450875,
        title="Психологічна допомога дорослим",
        photo=types.ChatPhotoEmpty(),
        date=datetime.datetime(2022, 1, 1, tzinfo=UTC),
        broadcast=False,
        megagroup=True,
        access_hash=123,
    )


def _owner():
    return types.ChannelParticipantCreator(
        user_id=ME_ID,
        admin_rights=types.ChatAdminRights(ban_users=True),
    )


def _member():
    return types.ChannelParticipant(
        user_id=TARGET_ID,
        date=datetime.datetime(2022, 1, 1, tzinfo=UTC),
    )


class FakeClient:
    def __init__(self, my_participant=None, target_participant=None):
        self.chat = _supergroup()
        self.me = types.User(id=ME_ID, is_self=True, first_name="Віталій")
        self.target = types.User(
            id=TARGET_ID,
            first_name="Vlad",
            last_name="Solomakha",
            username="vpznc",
        )
        self.my_participant = my_participant or _owner()
        self.target_participant = target_participant or _member()
        self.kicks = []

    async def get_me(self):
        return self.me

    async def kick_participant(self, entity, target):
        self.kicks.append((entity, target))
        self.target_participant = None


@pytest.fixture(autouse=True)
def clear_previews():
    groups._remove_member_previews.clear()


def _patch(monkeypatch, client):
    async def ensure_connected(cl):
        return None

    async def resolve_entity(identifier, cl):
        if identifier == CHAT_ID:
            return client.chat
        if identifier == TARGET_ID:
            return client.target
        raise AssertionError(f"Unexpected identifier: {identifier}")

    async def channel_participant(cl, entity, user):
        if user.id == ME_ID:
            return client.my_participant
        if user.id == TARGET_ID:
            return client.target_participant
        raise AssertionError(f"Unexpected user: {user.id}")

    monkeypatch.setattr(groups, "get_client", lambda account=None: client)
    monkeypatch.setattr(groups, "ensure_connected", ensure_connected)
    monkeypatch.setattr(groups, "resolve_entity", resolve_entity)
    monkeypatch.setattr(groups, "_channel_participant", channel_participant)
    monkeypatch.setattr(groups.secrets, "token_urlsafe", lambda size: "remove-token")


async def _preview(monkeypatch, client):
    _patch(monkeypatch, client)
    return json.loads(
        await groups.preview_remove_member_from_owned_group(
            chat_id=CHAT_ID,
            target_user_id=TARGET_ID,
        )
    )


@pytest.mark.asyncio
async def test_preview_is_read_only_and_scoped_to_owner_and_member(monkeypatch):
    client = FakeClient()

    payload = await _preview(monkeypatch, client)

    assert payload["status"] == "confirmation_required"
    assert payload["chat_id"] == CHAT_ID
    assert payload["target_user_id"] == TARGET_ID
    assert payload["target_role"] == "member"
    assert payload["messages_will_be_deleted"] is False
    assert payload["permanent_ban"] is False
    assert "REMOVE MEMBER" in payload["confirmation_phrase"]
    assert client.kicks == []


@pytest.mark.asyncio
async def test_execute_refuses_wrong_confirmation(monkeypatch):
    client = FakeClient()
    payload = await _preview(monkeypatch, client)

    result = await groups.remove_member_from_owned_group(
        chat_id=CHAT_ID,
        target_user_id=TARGET_ID,
        preview_token=payload["preview_token"],
        confirmation_phrase="yes",
    )

    assert result == "Refused: confirmation phrase does not exactly match the preview."
    assert client.kicks == []


@pytest.mark.asyncio
async def test_execute_rechecks_and_verifies_non_banning_removal(monkeypatch):
    client = FakeClient()
    payload = await _preview(monkeypatch, client)

    result = json.loads(
        await groups.remove_member_from_owned_group(
            chat_id=CHAT_ID,
            target_user_id=TARGET_ID,
            preview_token=payload["preview_token"],
            confirmation_phrase=payload["confirmation_phrase"],
        )
    )

    assert result["status"] == "complete"
    assert result["account_was_owner"] is True
    assert result["target_was_ordinary_member"] is True
    assert result["removed_from_group"] is True
    assert result["permanent_ban"] is False
    assert result["messages_deleted"] is False
    assert result["verified_after_removal"] is True
    assert len(client.kicks) == 1


@pytest.mark.asyncio
async def test_execute_refuses_if_ownership_changes_after_preview(monkeypatch):
    client = FakeClient()
    payload = await _preview(monkeypatch, client)
    client.my_participant = types.ChannelParticipant(
        user_id=ME_ID,
        date=datetime.datetime(2022, 1, 1, tzinfo=UTC),
    )

    result = await groups.remove_member_from_owned_group(
        chat_id=CHAT_ID,
        target_user_id=TARGET_ID,
        preview_token=payload["preview_token"],
        confirmation_phrase=payload["confirmation_phrase"],
    )

    assert result == "Refused: current account is no longer the group owner."
    assert client.kicks == []


@pytest.mark.asyncio
async def test_preview_refuses_admin_target(monkeypatch):
    client = FakeClient(
        target_participant=types.ChannelParticipantAdmin(
            user_id=TARGET_ID,
            promoted_by=ME_ID,
            date=datetime.datetime(2022, 1, 1, tzinfo=UTC),
            admin_rights=types.ChatAdminRights(ban_users=True),
        )
    )
    _patch(monkeypatch, client)

    result = await groups.preview_remove_member_from_owned_group(
        chat_id=CHAT_ID,
        target_user_id=TARGET_ID,
    )

    assert result == (
        "Refused: the target must be a current ordinary member; observed role is admin."
    )
    assert groups._remove_member_previews == {}
    assert client.kicks == []
