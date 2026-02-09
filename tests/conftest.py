"""Shared test fixtures for telegram-mcp test suite."""

import os
import sys
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timezone

# Set env vars BEFORE importing main
os.environ["TELEGRAM_API_ID"] = "12345"
os.environ["TELEGRAM_API_HASH"] = "test_hash_value"
os.environ["TELEGRAM_SESSION_STRING"] = "test_session_string"

# Patch TelegramClient and StringSession BEFORE main.py is imported
# main.py creates client at module level (line 73), so we must mock it early
_mock_module_client = AsyncMock()
_mock_module_client.is_connected.return_value = True
_mock_module_client.connect.return_value = None
_mock_module_client.start.return_value = None

_patcher_client = patch("telethon.TelegramClient", return_value=_mock_module_client)
_patcher_session = patch("telethon.sessions.StringSession", return_value=MagicMock())
_patcher_client.start()
_patcher_session.start()

# NOW it's safe to import main
import main


def _make_mock_user(user_id=100, first_name="Test", last_name="User", username="testuser", phone="1234567890"):
    user = MagicMock()
    user.id = user_id
    user.first_name = first_name
    user.last_name = last_name
    user.username = username
    user.phone = phone
    user.title = None
    user.bot = False
    user.status = MagicMock()
    user.status.__class__.__name__ = "UserStatusOnline"
    user.photo = MagicMock()
    return user


def _make_mock_chat(chat_id=200, title="Test Chat"):
    chat = MagicMock()
    chat.id = chat_id
    chat.title = title
    chat.first_name = None
    chat.username = None
    return chat


def _make_mock_message(msg_id=1, text="Hello", sender_id=100, chat_id=200, date=None):
    msg = MagicMock()
    msg.id = msg_id
    msg.message = text
    msg.text = text
    msg.date = date or datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    msg.media = None
    msg.from_id = MagicMock()
    msg.from_id.user_id = sender_id
    msg.sender = _make_mock_user(user_id=sender_id)
    msg.sender_id = sender_id
    msg.chat_id = chat_id
    msg.views = None
    msg.forwards = None
    msg.reactions = None
    msg.reply_to = None
    msg.forward = None
    msg.replies = None
    msg.pinned = False
    msg.buttons = None
    msg.reply_markup = None
    msg.peer_id = MagicMock()
    return msg


def _make_mock_dialog(dialog_id=200, title="Test Dialog", is_user=False):
    dialog = MagicMock()
    dialog.id = dialog_id
    dialog.title = title if not is_user else None
    dialog.name = title
    dialog.entity = _make_mock_user(user_id=dialog_id) if is_user else _make_mock_chat(chat_id=dialog_id, title=title)
    dialog.message = _make_mock_message(chat_id=dialog_id)
    dialog.unread_count = 0
    dialog.is_user = is_user
    dialog.is_group = not is_user
    dialog.is_channel = False
    return dialog


@pytest.fixture
def mock_client():
    """Create a fully mocked TelegramClient for tests."""
    mc = AsyncMock()

    # Connection
    mc.is_connected.return_value = True
    mc.connect.return_value = None
    mc.start.return_value = None
    mc.disconnect.return_value = None

    # Dialogs
    mc.get_dialogs.return_value = [_make_mock_dialog(), _make_mock_dialog(dialog_id=201, title="Chat 2")]

    # Entity
    mc.get_entity.return_value = _make_mock_user()
    mc.get_input_entity.return_value = MagicMock()

    # Messages
    mock_msgs = [_make_mock_message(msg_id=i, text=f"Message {i}") for i in range(1, 4)]
    mc.get_messages.return_value = mock_msgs
    mc.send_message.return_value = _make_mock_message(msg_id=99, text="sent")
    mc.edit_message.return_value = _make_mock_message(msg_id=1, text="edited")
    mc.delete_messages.return_value = MagicMock(pts_count=1)
    mc.forward_messages.return_value = [_make_mock_message(msg_id=50)]
    mc.pin_message.return_value = None
    mc.unpin_message.return_value = None
    mc.send_read_acknowledge.return_value = True

    # iter_messages — async iterator
    async def _iter_messages(*args, **kwargs):
        for m in mock_msgs:
            yield m
    mc.iter_messages = _iter_messages

    # Me
    mc.get_me.return_value = _make_mock_user(user_id=999, first_name="Me", username="me_user")

    # Participants
    mc.get_participants.return_value = [_make_mock_user(user_id=i) for i in range(1, 4)]

    # Files
    mc.send_file.return_value = _make_mock_message(msg_id=70, text="file sent")
    mc.download_media.return_value = "/tmp/downloaded_file.jpg"
    mc.upload_file.return_value = MagicMock()

    # Common chats
    mc.get_common_chats.return_value = [_make_mock_chat()]

    # Export invite
    mc.export_chat_invite_link.return_value = "https://t.me/joinchat/abc123"

    # RPC calls: client(functions.xxx) — use __call__
    rpc_result = MagicMock()
    rpc_result.users = [_make_mock_user()]
    rpc_result.chats = [_make_mock_chat()]
    rpc_result.updates = []
    rpc_result.id = 300
    rpc_result.link = "https://t.me/joinchat/xyz"
    rpc_result.full_user = MagicMock()
    rpc_result.full_user.about = "Test about"
    rpc_result.full_user.common_chats_count = 1
    rpc_result.full_chat = MagicMock()
    rpc_result.full_chat.about = "Group about"

    # contacts results
    rpc_result.contacts = []
    rpc_result.imported = []
    rpc_result.blocked = MagicMock()
    rpc_result.blocked.count = 0

    # stickers
    rpc_result.sets = []

    # dialog filters
    rpc_result.filters = []

    # drafts
    rpc_result.drafts = []

    # photos
    rpc_result.photos = []
    rpc_result.photo = MagicMock()
    rpc_result.photo.id = 1

    mc.return_value = rpc_result

    # Event handler registration
    mc.on = MagicMock(return_value=lambda f: f)
    mc.add_event_handler = MagicMock()
    mc.remove_event_handler = MagicMock()

    return mc


@pytest.fixture
def patched_main(mock_client):
    """Provide main module with a fresh mock client patched in."""
    original_client = main.client
    main.client = mock_client
    yield main
    main.client = original_client
