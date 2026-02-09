"""Tests for watcher infrastructure — watch_user, unwatch_user, check_watched_messages, list_watched_users."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

import main


@pytest.fixture(autouse=True)
def reset_watcher_state():
    """Reset global watcher state before each test."""
    main._watched_users.clear()
    main._watched_messages.clear()
    main._watcher_handler = None
    yield
    main._watched_users.clear()
    main._watched_messages.clear()
    main._watcher_handler = None


@pytest.fixture
def watcher_client():
    """Mock client for watcher tests with is_connected as sync method."""
    mc = AsyncMock()
    mc.is_connected = lambda: True

    user = MagicMock()
    user.id = 302676
    user.first_name = "Anatoly"
    user.last_name = "Skornyakov"
    user.username = "tolik"
    user.title = None
    mc.get_entity.return_value = user

    mc.add_event_handler = MagicMock(return_value="handler_ref")
    mc.remove_event_handler = MagicMock()

    return mc


# --- watch_user tests ---


@pytest.mark.asyncio
async def test_watch_user_adds_to_dict(watcher_client):
    with patch.object(main, "client", watcher_client):
        result = await main.watch_user(user_id=302676)
        assert isinstance(result, str)
        assert "Anatoly" in result
        assert 302676 in main._watched_users


@pytest.mark.asyncio
async def test_watch_user_with_chat_filter(watcher_client):
    with patch.object(main, "client", watcher_client):
        result = await main.watch_user(user_id=302676, chat_id=500)
        assert "chat 500" in result
        assert main._watched_users[302676]["chat_id"] == 500


@pytest.mark.asyncio
async def test_watch_user_with_label(watcher_client):
    with patch.object(main, "client", watcher_client):
        result = await main.watch_user(user_id=302676, label="Tolik response")
        assert main._watched_users[302676]["label"] == "Tolik response"


@pytest.mark.asyncio
async def test_watch_user_duplicate_overwrites(watcher_client):
    with patch.object(main, "client", watcher_client):
        await main.watch_user(user_id=302676, label="first")
        await main.watch_user(user_id=302676, label="second")
        assert main._watched_users[302676]["label"] == "second"


@pytest.mark.asyncio
async def test_watch_user_registers_event_handler(watcher_client):
    with patch.object(main, "client", watcher_client):
        await main.watch_user(user_id=302676)
        watcher_client.add_event_handler.assert_called_once()
        assert main._watcher_handler is not None


@pytest.mark.asyncio
async def test_watch_user_second_watch_no_duplicate_handler(watcher_client):
    with patch.object(main, "client", watcher_client):
        await main.watch_user(user_id=302676)
        # Set up a second user
        user2 = MagicMock()
        user2.id = 999
        user2.first_name = "Other"
        user2.title = None
        watcher_client.get_entity.return_value = user2
        await main.watch_user(user_id=999)
        # add_event_handler called only once (for first watch)
        assert watcher_client.add_event_handler.call_count == 1


# --- unwatch_user tests ---


@pytest.mark.asyncio
async def test_unwatch_user_removes_from_dict(watcher_client):
    with patch.object(main, "client", watcher_client):
        await main.watch_user(user_id=302676)
        result = await main.unwatch_user(user_id=302676)
        assert "Stopped watching" in result
        assert 302676 not in main._watched_users


@pytest.mark.asyncio
async def test_unwatch_user_not_found(watcher_client):
    with patch.object(main, "client", watcher_client):
        result = await main.unwatch_user(user_id=302676)
        assert "not being watched" in result


@pytest.mark.asyncio
async def test_unwatch_user_last_removes_handler(watcher_client):
    with patch.object(main, "client", watcher_client):
        await main.watch_user(user_id=302676)
        await main.unwatch_user(user_id=302676)
        watcher_client.remove_event_handler.assert_called_once()
        assert main._watcher_handler is None


# --- list_watched_users tests ---


@pytest.mark.asyncio
async def test_list_watched_users_empty(watcher_client):
    with patch.object(main, "client", watcher_client):
        result = await main.list_watched_users()
        assert "No users" in result


@pytest.mark.asyncio
async def test_list_watched_users_shows_all(watcher_client):
    with patch.object(main, "client", watcher_client):
        await main.watch_user(user_id=302676, label="Tolik")
        result = await main.list_watched_users()
        assert "1 watched user" in result
        assert "302676" in result
        assert "Tolik" in result


# --- check_watched_messages tests ---


@pytest.mark.asyncio
async def test_check_watched_messages_empty(watcher_client):
    with patch.object(main, "client", watcher_client):
        result = await main.check_watched_messages()
        assert "No new messages" in result


@pytest.mark.asyncio
async def test_check_watched_messages_returns_all(watcher_client):
    main._watched_messages.append({
        "user_id": 302676,
        "chat_id": 500,
        "message_id": 1,
        "text": "Hello there",
        "date": "2026-02-09T18:00:00+00:00",
        "sender_name": "Anatoly",
    })
    with patch.object(main, "client", watcher_client):
        result = await main.check_watched_messages()
        assert "1 message(s)" in result
        assert "Hello there" in result


@pytest.mark.asyncio
async def test_check_watched_messages_filter_by_user(watcher_client):
    main._watched_messages.extend([
        {
            "user_id": 302676, "chat_id": 500, "message_id": 1,
            "text": "From Tolik", "date": "2026-02-09T18:00:00+00:00", "sender_name": "Anatoly",
        },
        {
            "user_id": 999, "chat_id": 500, "message_id": 2,
            "text": "From Other", "date": "2026-02-09T18:01:00+00:00", "sender_name": "Other",
        },
    ])
    with patch.object(main, "client", watcher_client):
        result = await main.check_watched_messages(user_id=302676)
        assert "1 message(s)" in result
        assert "From Tolik" in result
        assert "From Other" not in result


@pytest.mark.asyncio
async def test_check_watched_messages_clears_queue(watcher_client):
    main._watched_messages.append({
        "user_id": 302676, "chat_id": 500, "message_id": 1,
        "text": "Test", "date": "2026-02-09T18:00:00+00:00", "sender_name": "Anatoly",
    })
    with patch.object(main, "client", watcher_client):
        await main.check_watched_messages()
        assert len(main._watched_messages) == 0


@pytest.mark.asyncio
async def test_check_watched_messages_keeps_queue(watcher_client):
    main._watched_messages.append({
        "user_id": 302676, "chat_id": 500, "message_id": 1,
        "text": "Test", "date": "2026-02-09T18:00:00+00:00", "sender_name": "Anatoly",
    })
    with patch.object(main, "client", watcher_client):
        await main.check_watched_messages(keep=True)
        assert len(main._watched_messages) == 1


# --- _on_watched_message event handler tests ---


@pytest.mark.asyncio
async def test_on_watched_message_captures_message():
    main._watched_users[302676] = {"chat_id": None, "label": "Tolik", "name": "Anatoly"}

    event = AsyncMock()
    event.sender_id = 302676
    event.chat_id = 500
    event.message = MagicMock()
    event.message.id = 42
    event.message.text = "Hey, got your message"
    event.message.date = datetime(2026, 2, 9, 18, 0, 0, tzinfo=timezone.utc)
    sender = MagicMock()
    sender.first_name = "Anatoly"
    event.get_sender.return_value = sender

    await main._on_watched_message(event)

    assert len(main._watched_messages) == 1
    msg = main._watched_messages[0]
    assert msg["user_id"] == 302676
    assert msg["text"] == "Hey, got your message"
    assert msg["message_id"] == 42


@pytest.mark.asyncio
async def test_on_watched_message_ignores_unwatched_user():
    event = AsyncMock()
    event.sender_id = 999999

    await main._on_watched_message(event)
    assert len(main._watched_messages) == 0


@pytest.mark.asyncio
async def test_on_watched_message_respects_chat_filter():
    main._watched_users[302676] = {"chat_id": 500, "label": "Tolik", "name": "Anatoly"}

    event = AsyncMock()
    event.sender_id = 302676
    event.chat_id = 999  # Wrong chat
    event.message = MagicMock()
    event.message.id = 1
    event.message.text = "Wrong chat"
    event.message.date = datetime(2026, 2, 9, 18, 0, 0, tzinfo=timezone.utc)

    await main._on_watched_message(event)
    assert len(main._watched_messages) == 0


@pytest.mark.asyncio
async def test_on_watched_message_no_chat_filter_captures_all():
    main._watched_users[302676] = {"chat_id": None, "label": "Tolik", "name": "Anatoly"}

    for chat_id in [100, 200, 300]:
        event = AsyncMock()
        event.sender_id = 302676
        event.chat_id = chat_id
        event.message = MagicMock()
        event.message.id = chat_id
        event.message.text = f"From chat {chat_id}"
        event.message.date = datetime(2026, 2, 9, 18, 0, 0, tzinfo=timezone.utc)
        sender = MagicMock()
        sender.first_name = "Anatoly"
        event.get_sender.return_value = sender
        await main._on_watched_message(event)

    assert len(main._watched_messages) == 3


@pytest.mark.asyncio
async def test_on_watched_message_handles_none_text():
    main._watched_users[302676] = {"chat_id": None, "label": "Tolik", "name": "Anatoly"}

    event = AsyncMock()
    event.sender_id = 302676
    event.chat_id = 500
    event.message = MagicMock()
    event.message.id = 1
    event.message.text = None
    event.message.date = datetime(2026, 2, 9, 18, 0, 0, tzinfo=timezone.utc)
    sender = MagicMock()
    sender.first_name = "Anatoly"
    event.get_sender.return_value = sender

    await main._on_watched_message(event)
    assert main._watched_messages[0]["text"] == ""


@pytest.mark.asyncio
async def test_on_watched_message_handles_none_date():
    main._watched_users[302676] = {"chat_id": None, "label": "Tolik", "name": "Anatoly"}

    event = AsyncMock()
    event.sender_id = 302676
    event.chat_id = 500
    event.message = MagicMock()
    event.message.id = 1
    event.message.text = "test"
    event.message.date = None
    sender = MagicMock()
    sender.first_name = "Anatoly"
    event.get_sender.return_value = sender

    await main._on_watched_message(event)
    assert main._watched_messages[0]["date"] is None


# --- Integration-style tests ---


@pytest.mark.asyncio
async def test_watch_then_check_flow(watcher_client):
    """Full flow: watch → simulate message → check."""
    with patch.object(main, "client", watcher_client):
        await main.watch_user(user_id=302676)

        # Simulate message arrival
        event = AsyncMock()
        event.sender_id = 302676
        event.chat_id = 500
        event.message = MagicMock()
        event.message.id = 42
        event.message.text = "Reply from Tolik"
        event.message.date = datetime(2026, 2, 9, 18, 0, 0, tzinfo=timezone.utc)
        sender = MagicMock()
        sender.first_name = "Anatoly"
        event.get_sender.return_value = sender
        await main._on_watched_message(event)

        result = await main.check_watched_messages()
        assert "1 message(s)" in result
        assert "Reply from Tolik" in result


@pytest.mark.asyncio
async def test_watch_unwatch_check_empty(watcher_client):
    """Watch → unwatch → message arrives → check should be empty (handler removed)."""
    with patch.object(main, "client", watcher_client):
        await main.watch_user(user_id=302676)
        await main.unwatch_user(user_id=302676)

        # Simulate message — should be ignored since user is unwatched
        event = AsyncMock()
        event.sender_id = 302676
        event.chat_id = 500
        event.message = MagicMock()
        event.message.id = 42
        event.message.text = "This should be ignored"
        event.message.date = datetime(2026, 2, 9, 18, 0, 0, tzinfo=timezone.utc)
        await main._on_watched_message(event)

        result = await main.check_watched_messages()
        assert "No new messages" in result


@pytest.mark.asyncio
async def test_multiple_watchers_independent(watcher_client):
    """Multiple watchers should work independently."""
    with patch.object(main, "client", watcher_client):
        await main.watch_user(user_id=302676, label="Tolik")

        # Add second user
        user2 = MagicMock()
        user2.id = 999
        user2.first_name = "Other"
        user2.title = None
        watcher_client.get_entity.return_value = user2
        await main.watch_user(user_id=999, label="Other")

        assert len(main._watched_users) == 2

        # Simulate messages from both
        for uid, name in [(302676, "Anatoly"), (999, "Other")]:
            event = AsyncMock()
            event.sender_id = uid
            event.chat_id = 500
            event.message = MagicMock()
            event.message.id = uid
            event.message.text = f"From {name}"
            event.message.date = datetime(2026, 2, 9, 18, 0, 0, tzinfo=timezone.utc)
            sender = MagicMock()
            sender.first_name = name
            event.get_sender.return_value = sender
            await main._on_watched_message(event)

        assert len(main._watched_messages) == 2

        # Check filtered
        watcher_client.get_entity.return_value = MagicMock(id=302676)
        result = await main.check_watched_messages(user_id=302676)
        assert "1 message(s)" in result
        assert "From Anatoly" in result
