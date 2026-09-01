"""Tests for privacy-scoped Telegram voice and video-note transcription."""

import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from telethon import errors, functions, types

from telegram_mcp import runtime
from telegram_mcp.tools import media


@pytest.fixture(autouse=True)
def reset_transcription_state():
    media._transcription_cache.clear()
    media._transcription_tokens_by_id.clear()
    media._transcription_waiters.clear()
    media._transcription_handler_clients.clear()
    yield
    media._transcription_cache.clear()
    media._transcription_tokens_by_id.clear()
    media._transcription_waiters.clear()
    media._transcription_handler_clients.clear()


def make_message(*, voice=False, video_note=False, audio=False, video=False):
    message = MagicMock()
    message.id = 42
    message.media = MagicMock()
    message.voice = MagicMock() if voice else None
    message.video_note = MagicMock() if video_note else None
    message.audio = MagicMock() if audio else None
    message.video = MagicMock() if video else None
    return message


def make_client(message, rpc_result=None):
    client = AsyncMock()
    client.is_connected = lambda: True
    client.get_input_entity.return_value = MagicMock(name="peer")
    client.get_messages.return_value = message
    client.add_event_handler = MagicMock()
    client.return_value = rpc_result
    return client


def install_client(monkeypatch, client):
    monkeypatch.setattr(media, "get_client", lambda account=None: client)
    monkeypatch.setattr(media, "ensure_connected", AsyncMock())

    async def resolve_input_entity(chat_id, selected_client):
        assert selected_client is client
        return MagicMock(name=f"peer:{chat_id}")

    monkeypatch.setattr(media, "resolve_input_entity", resolve_input_entity)


def parse(result):
    return json.loads(result)


def test_tools_are_registered_with_expected_safety_annotations():
    tools = {tool.name: tool for tool in runtime.mcp._tool_manager.list_tools()}

    transcribe = tools["transcribe_voice_or_video_note"].annotations
    assert transcribe.openWorldHint is True
    assert transcribe.readOnlyHint is False
    assert transcribe.destructiveHint is False

    status = tools["get_media_transcription_status"].annotations
    assert status.openWorldHint is False
    assert status.readOnlyHint is True
    assert status.destructiveHint is False


@pytest.mark.asyncio
async def test_confirmation_required_makes_no_telegram_calls(monkeypatch):
    client = make_client(make_message(voice=True))
    install_client(monkeypatch, client)

    result = parse(
        await media.transcribe_voice_or_video_note(
            chat_id=100, message_id=42, confirm_transcription=False
        )
    )

    assert result["status"] == "confirmation_required"
    media.ensure_connected.assert_not_awaited()
    client.get_input_entity.assert_not_called()
    client.get_messages.assert_not_called()
    client.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("message", "media_type"),
    [
        (make_message(voice=True), "voice"),
        (make_message(video_note=True, video=True), "video_note"),
    ],
)
async def test_ready_transcription_supports_voice_and_video_note(monkeypatch, message, media_type):
    rpc_result = types.messages.TranscribedAudio(
        transcription_id=9001,
        text="Тестовий текст",
        pending=False,
        trial_remains_num=4,
        trial_remains_until_date=datetime(2026, 9, 2, tzinfo=timezone.utc),
    )
    client = make_client(message, rpc_result)
    install_client(monkeypatch, client)

    result = parse(
        await media.transcribe_voice_or_video_note(
            chat_id=100, message_id=42, confirm_transcription=True
        )
    )

    assert result == {
        "status": "completed",
        "pending": False,
        "transcription_id": 9001,
        "text": "Тестовий текст",
        "media_type": media_type,
        "chat_id": 100,
        "message_id": 42,
        "trial_remains_num": 4,
        "trial_remains_until_date": "2026-09-02T00:00:00+00:00",
    }
    request = client.await_args.args[0]
    assert isinstance(request, functions.messages.TranscribeAudioRequest)
    assert request.msg_id == 42
    client.download_media.assert_not_called()


@pytest.mark.asyncio
async def test_transcript_text_is_sanitized(monkeypatch):
    rpc_result = types.messages.TranscribedAudio(
        transcription_id=9010,
        text="  видимий\u200b текст  ",
        pending=False,
    )
    client = make_client(make_message(voice=True), rpc_result)
    install_client(monkeypatch, client)

    result = parse(
        await media.transcribe_voice_or_video_note(
            chat_id=100, message_id=42, confirm_transcription=True
        )
    )

    assert result["text"] == "видимий текст"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message",
    [make_message(audio=True), make_message(video=True), make_message()],
)
async def test_ordinary_media_is_rejected_before_transcription_rpc(monkeypatch, message):
    client = make_client(message)
    install_client(monkeypatch, client)

    result = parse(
        await media.transcribe_voice_or_video_note(
            chat_id=100, message_id=42, confirm_transcription=True
        )
    )

    assert result["status"] == "error"
    assert result["error"] == "unsupported_media_type"
    client.assert_not_awaited()
    client.download_media.assert_not_called()


@pytest.mark.asyncio
async def test_pending_transcription_waits_for_matching_final_update(monkeypatch):
    rpc_result = types.messages.TranscribedAudio(
        transcription_id=9002, text="Чернетка", pending=True
    )
    client = make_client(make_message(voice=True), rpc_result)
    install_client(monkeypatch, client)

    async def deliver_update():
        cache_key = (id(client), 9002)
        while cache_key not in media._transcription_tokens_by_id:
            await asyncio.sleep(0)
        await media._on_transcribed_audio(
            id(client),
            types.UpdateTranscribedAudio(
                peer=types.PeerUser(100),
                msg_id=42,
                transcription_id=9002,
                text="Готовий текст",
                pending=False,
            ),
        )

    delivery = asyncio.create_task(deliver_update())
    result = parse(
        await media.transcribe_voice_or_video_note(
            chat_id=100, message_id=42, confirm_transcription=True
        )
    )
    await delivery

    assert result["status"] == "completed"
    assert result["text"] == "Готовий текст"
    assert client.add_event_handler.call_count == 1


@pytest.mark.asyncio
async def test_pending_timeout_returns_partial_and_status_token(monkeypatch):
    rpc_result = types.messages.TranscribedAudio(
        transcription_id=9003, text="Частина", pending=True
    )
    client = make_client(make_message(video_note=True, video=True), rpc_result)
    install_client(monkeypatch, client)
    monkeypatch.setattr(media, "TRANSCRIPTION_WAIT_TIMEOUT_SECONDS", 0)

    result = parse(
        await media.transcribe_voice_or_video_note(
            chat_id=100, message_id=42, confirm_transcription=True
        )
    )
    status = parse(await media.get_media_transcription_status(result["status_token"]))

    assert result["status"] == "pending"
    assert result["text"] == "Частина"
    assert status["status"] == "pending"
    assert media._transcription_cache[result["status_token"]]["expiry_handle"]
    client.assert_awaited_once()


@pytest.mark.asyncio
async def test_partial_update_uses_only_transcription_id_then_final_completes(
    monkeypatch,
):
    rpc_result = types.messages.TranscribedAudio(transcription_id=9004, text="", pending=True)
    client = make_client(make_message(voice=True), rpc_result)
    install_client(monkeypatch, client)

    async def deliver_updates():
        cache_key = (id(client), 9004)
        while cache_key not in media._transcription_tokens_by_id:
            await asyncio.sleep(0)
        await media._on_transcribed_audio(
            id(client),
            types.UpdateTranscribedAudio(
                peer=types.PeerUser(999),
                msg_id=999,
                transcription_id=9004,
                text="Частина",
                pending=True,
            ),
        )
        await media._on_transcribed_audio(
            id(client),
            types.UpdateTranscribedAudio(
                peer=types.PeerUser(888),
                msg_id=888,
                transcription_id=9004,
                text="Фінал",
                pending=False,
            ),
        )

    delivery = asyncio.create_task(deliver_updates())
    result = parse(
        await media.transcribe_voice_or_video_note(
            chat_id=100, message_id=42, confirm_transcription=True
        )
    )
    await delivery

    assert result["status"] == "completed"
    assert result["text"] == "Фінал"


@pytest.mark.asyncio
async def test_concurrent_requests_with_same_transcription_id_both_complete(
    monkeypatch,
):
    rpc_result = types.messages.TranscribedAudio(transcription_id=9008, text="", pending=True)
    client = make_client(make_message(voice=True), rpc_result)
    install_client(monkeypatch, client)
    cache_key = (id(client), 9008)

    async def deliver_update():
        while len(media._transcription_tokens_by_id.get(cache_key, ())) < 2:
            await asyncio.sleep(0)
        await media._on_transcribed_audio(
            id(client),
            types.UpdateTranscribedAudio(
                peer=types.PeerUser(100),
                msg_id=42,
                transcription_id=9008,
                text="Один фінал",
                pending=False,
            ),
        )

    delivery = asyncio.create_task(deliver_update())
    first, second = await asyncio.gather(
        media.transcribe_voice_or_video_note(100, 42, True),
        media.transcribe_voice_or_video_note(100, 42, True),
    )
    await delivery

    assert parse(first)["text"] == "Один фінал"
    assert parse(second)["text"] == "Один фінал"
    assert cache_key not in media._transcription_tokens_by_id


@pytest.mark.asyncio
async def test_unknown_transcription_id_is_ignored():
    await media._on_transcribed_audio(
        123,
        types.UpdateTranscribedAudio(
            peer=types.PeerUser(100),
            msg_id=42,
            transcription_id=9999,
            text="Не наш текст",
            pending=False,
        ),
    )

    assert media._transcription_cache == {}
    assert media._transcription_tokens_by_id == {}


@pytest.mark.asyncio
async def test_handler_is_registered_only_once_per_client(monkeypatch):
    rpc_result = types.messages.TranscribedAudio(
        transcription_id=9005, text="Готово", pending=False
    )
    client = make_client(make_message(voice=True), rpc_result)
    install_client(monkeypatch, client)

    await media.transcribe_voice_or_video_note(100, 42, True)
    await media.transcribe_voice_or_video_note(100, 42, True)

    client.add_event_handler.assert_called_once()


@pytest.mark.asyncio
async def test_expired_or_restart_status_token_is_unknown(monkeypatch):
    cache_key = (123, 9006)
    media._transcription_cache["expired"] = {
        "expires_at": 10.0,
        "transcription_id": 9006,
        "client_id": 123,
        "pending": True,
    }
    media._transcription_tokens_by_id[cache_key] = {"expired"}
    monkeypatch.setattr(media.time, "monotonic", lambda: 11.0)

    expired = parse(await media.get_media_transcription_status("expired"))
    after_restart = parse(await media.get_media_transcription_status("missing"))

    assert expired == {
        "status": "unknown",
        "error": "status_token_unknown_or_expired",
    }
    assert after_restart == expired
    assert cache_key not in media._transcription_tokens_by_id


@pytest.mark.asyncio
async def test_scheduled_expiry_removes_transcript_without_status_poll():
    cache_key = (123, 9007)
    media._transcription_cache["scheduled"] = {
        "expires_at": 10.0,
        "transcription_id": 9007,
        "client_id": 123,
        "pending": True,
    }
    media._transcription_tokens_by_id[cache_key] = {"scheduled"}

    asyncio.get_running_loop().call_soon(media._expire_transcription_token, "scheduled")
    await asyncio.sleep(0)

    assert "scheduled" not in media._transcription_cache
    assert cache_key not in media._transcription_tokens_by_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "expected", "seconds"),
    [
        (errors.BadRequestError(None, "MSG_ID_INVALID"), "message_not_found", None),
        (
            errors.BadRequestError(None, "PEER_ID_INVALID"),
            "chat_not_found_or_unavailable",
            None,
        ),
        (
            errors.BadRequestError(None, "MSG_VOICE_MISSING"),
            "unsupported_media_type",
            None,
        ),
        (errors.BadRequestError(None, "MSG_VOICE_TOO_LONG"), "voice_too_long", None),
        (
            errors.PremiumAccountRequiredError(None),
            "transcription_not_entitled",
            None,
        ),
        (
            errors.BadRequestError(None, "TRANSCRIPTION_FAILED"),
            "transcription_failed",
            None,
        ),
        (errors.FloodWaitError(None, capture=17), "rate_limited", 17),
    ],
)
async def test_rpc_errors_are_mapped_without_transcript_logging(
    monkeypatch, error, expected, seconds
):
    client = make_client(make_message(voice=True))
    client.side_effect = error
    install_client(monkeypatch, client)
    log_error = MagicMock()
    monkeypatch.setattr(media.logger, "error", log_error)

    result = parse(
        await media.transcribe_voice_or_video_note(
            chat_id=100, message_id=42, confirm_transcription=True
        )
    )

    assert result["status"] == "error"
    assert result["error"] == expected
    if seconds is not None:
        assert result["retry_after_seconds"] == seconds
    assert "Тестовий текст" not in str(log_error.call_args_list)
    client.download_media.assert_not_called()
