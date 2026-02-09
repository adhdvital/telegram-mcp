"""Tests for auto_reconnect and validate_id decorators."""

import pytest
from unittest.mock import AsyncMock, patch

import main
from main import auto_reconnect, validate_id, ValidationError


# --- auto_reconnect tests ---


@pytest.mark.asyncio
async def test_auto_reconnect_connected():
    """When client is connected, function is called directly."""
    mock_func = AsyncMock(return_value="ok")
    mock_func.__name__ = "mock_func"
    mock_func.__qualname__ = "mock_func"
    mock_func.__module__ = "test"
    decorated = auto_reconnect(mock_func)

    mock_client = AsyncMock()
    # is_connected is a sync method in Telethon, must be non-async
    mock_client.is_connected = lambda: True

    with patch.object(main, "client", mock_client):
        result = await decorated()
        assert result == "ok"
        mock_client.connect.assert_not_called()
        mock_func.assert_called_once()


@pytest.mark.asyncio
async def test_auto_reconnect_disconnected():
    """When client is disconnected, reconnects then calls function."""
    mock_func = AsyncMock(return_value="reconnected ok")
    mock_func.__name__ = "mock_func"
    mock_func.__qualname__ = "mock_func"
    mock_func.__module__ = "test"
    decorated = auto_reconnect(mock_func)

    mock_client = AsyncMock()
    # is_connected must be a regular function (not coroutine) returning False
    mock_client.is_connected = lambda: False

    with patch.object(main, "client", mock_client):
        result = await decorated()
        assert result == "reconnected ok"
        mock_client.connect.assert_called_once()


# --- validate_id tests ---


@pytest.mark.asyncio
async def test_validate_id_passes_through_valid_int():
    @validate_id("user_id")
    async def func(**kwargs):
        return kwargs["user_id"]

    result = await func(user_id=12345)
    assert result == 12345


@pytest.mark.asyncio
async def test_validate_id_converts_string_int():
    @validate_id("chat_id")
    async def func(**kwargs):
        return kwargs["chat_id"]

    result = await func(chat_id="67890")
    assert result == 67890


@pytest.mark.asyncio
async def test_validate_id_passes_username():
    @validate_id("user_id")
    async def func(**kwargs):
        return kwargs["user_id"]

    result = await func(user_id="@test_user")
    assert result == "@test_user"


@pytest.mark.asyncio
async def test_validate_id_rejects_float():
    @validate_id("user_id")
    async def func(**kwargs):
        return "should not reach"

    result = await func(user_id=3.14)
    assert isinstance(result, str)
    assert "Invalid" in result


@pytest.mark.asyncio
async def test_validate_id_rejects_short_string():
    @validate_id("user_id")
    async def func(**kwargs):
        return "should not reach"

    result = await func(user_id="ab")
    assert isinstance(result, str)
    assert "Invalid" in result


@pytest.mark.asyncio
async def test_validate_id_skips_none():
    @validate_id("user_id")
    async def func(**kwargs):
        return "ok"

    result = await func(user_id=None)
    assert result == "ok"


@pytest.mark.asyncio
async def test_validate_id_skips_missing():
    @validate_id("user_id")
    async def func(**kwargs):
        return "ok"

    result = await func()
    assert result == "ok"
