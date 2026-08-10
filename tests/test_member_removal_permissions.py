import datetime
import json
from types import SimpleNamespace

import pytest
from telethon.tl import functions, types

from telegram_mcp.tools import groups


UTC = datetime.timezone.utc
ME_ID = 31848766
TARGET_ID = 118996429


def _basic_group():
    return types.Chat(
        id=738504771,
        title="Mindist Syndicate",
        photo=types.ChatPhotoEmpty(),
        participants_count=6,
        date=datetime.datetime(2021, 11, 21, tzinfo=UTC),
        version=1,
    )


def _supergroup():
    return types.Channel(
        id=1758980954,
        title="Mindist general",
        photo=types.ChatPhotoEmpty(),
        date=datetime.datetime(2022, 1, 1, tzinfo=UTC),
        broadcast=False,
        megagroup=True,
        access_hash=123,
    )


def _target():
    return types.User(
        id=TARGET_ID,
        first_name="Tanya",
        last_name="Chaykovskaya",
        username="tanichkachay",
    )


class FakeClient:
    def __init__(self, chat, my_participant, target_participant):
        self.chat = chat
        self.me = types.User(id=ME_ID, is_self=True, first_name="Віталій")
        self.target = _target()
        self.my_participant = my_participant
        self.target_participant = target_participant
        self.requests = []

    async def get_me(self):
        return self.me

    async def __call__(self, request):
        self.requests.append(request)
        if isinstance(request, functions.messages.GetFullChatRequest):
            container = types.ChatParticipants(
                chat_id=self.chat.id,
                participants=[self.my_participant, self.target_participant],
                version=1,
            )
            return SimpleNamespace(full_chat=SimpleNamespace(participants=container))
        if isinstance(request, functions.channels.GetParticipantRequest):
            participant_id = getattr(request.participant, "id", request.participant)
            participant = (
                self.my_participant if participant_id == ME_ID else self.target_participant
            )
            return SimpleNamespace(participant=participant)
        raise AssertionError(f"Unexpected request: {request!r}")


def _patch(monkeypatch, client):
    async def ensure_connected(cl):
        return None

    async def resolve_entity(identifier, cl):
        if identifier == -client.chat.id or identifier == -1000000000000 - client.chat.id:
            return client.chat
        if identifier == TARGET_ID:
            return client.target
        raise AssertionError(f"Unexpected identifier: {identifier}")

    monkeypatch.setattr(groups, "get_client", lambda account=None: client)
    monkeypatch.setattr(groups, "ensure_connected", ensure_connected)
    monkeypatch.setattr(groups, "resolve_entity", resolve_entity)


@pytest.mark.asyncio
async def test_basic_group_owner_can_remove_admin_target(monkeypatch):
    chat = _basic_group()
    client = FakeClient(
        chat,
        types.ChatParticipantCreator(user_id=ME_ID),
        types.ChatParticipantAdmin(
            user_id=TARGET_ID,
            inviter_id=ME_ID,
            date=datetime.datetime(2021, 11, 21, tzinfo=UTC),
        ),
    )
    _patch(monkeypatch, client)

    result = json.loads(
        await groups.check_member_removal_permissions(
            chat_id=-chat.id,
            target_user_id=TARGET_ID,
        )
    )

    assert result["my_role"] == "owner"
    assert result["target_role"] == "admin"
    assert result["can_remove_target"] is True
    assert result["owner_and_can_remove_target"] is True
    assert result["read_only"] is True


@pytest.mark.asyncio
async def test_basic_group_member_cannot_remove_target(monkeypatch):
    chat = _basic_group()
    client = FakeClient(
        chat,
        types.ChatParticipant(
            user_id=ME_ID,
            inviter_id=TARGET_ID,
            date=datetime.datetime(2021, 11, 21, tzinfo=UTC),
        ),
        types.ChatParticipantCreator(user_id=TARGET_ID),
    )
    _patch(monkeypatch, client)

    result = json.loads(
        await groups.check_member_removal_permissions(
            chat_id=-chat.id,
            target_user_id=TARGET_ID,
        )
    )

    assert result["my_role"] == "member"
    assert result["target_role"] == "owner"
    assert result["can_remove_target"] is False
    assert result["owner_and_can_remove_target"] is False


@pytest.mark.asyncio
async def test_supergroup_admin_does_not_claim_peer_admin_is_removable(monkeypatch):
    chat = _supergroup()
    rights = types.ChatAdminRights(ban_users=True)
    client = FakeClient(
        chat,
        types.ChannelParticipantAdmin(
            user_id=ME_ID,
            promoted_by=999,
            date=datetime.datetime(2022, 1, 1, tzinfo=UTC),
            admin_rights=rights,
        ),
        types.ChannelParticipantAdmin(
            user_id=TARGET_ID,
            promoted_by=999,
            date=datetime.datetime(2022, 1, 1, tzinfo=UTC),
            admin_rights=rights,
        ),
    )
    _patch(monkeypatch, client)

    result = json.loads(
        await groups.check_member_removal_permissions(
            chat_id=-1000000000000 - chat.id,
            target_user_id=TARGET_ID,
        )
    )

    assert result["my_role"] == "admin"
    assert result["my_can_ban_users"] is True
    assert result["target_role"] == "admin"
    assert result["can_remove_target"] is False
    assert result["owner_and_can_remove_target"] is False


@pytest.mark.asyncio
async def test_supergroup_owner_can_remove_member(monkeypatch):
    chat = _supergroup()
    client = FakeClient(
        chat,
        types.ChannelParticipantCreator(
            user_id=ME_ID,
            admin_rights=types.ChatAdminRights(ban_users=True),
        ),
        types.ChannelParticipant(
            user_id=TARGET_ID,
            date=datetime.datetime(2022, 1, 1, tzinfo=UTC),
        ),
    )
    _patch(monkeypatch, client)

    result = json.loads(
        await groups.check_member_removal_permissions(
            chat_id=-1000000000000 - chat.id,
            target_user_id=TARGET_ID,
        )
    )

    assert result["my_role"] == "owner"
    assert result["target_role"] == "member"
    assert result["can_remove_target"] is True
    assert result["owner_and_can_remove_target"] is True
