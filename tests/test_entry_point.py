"""Tests for entry point functions (_main and main)."""

import sqlite3
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import main


@pytest.mark.asyncio
async def test_main_starts_client():
    """_main() should call client.start()."""
    mock_client = AsyncMock()
    mock_mcp = AsyncMock()

    with patch.object(main, "client", mock_client), \
         patch.object(main, "mcp", mock_mcp):
        await main._main()
        mock_client.start.assert_called_once()


@pytest.mark.asyncio
async def test_main_runs_mcp_server():
    """_main() should call mcp.run_stdio_async()."""
    mock_client = AsyncMock()
    mock_mcp = AsyncMock()

    with patch.object(main, "client", mock_client), \
         patch.object(main, "mcp", mock_mcp):
        await main._main()
        mock_mcp.run_stdio_async.assert_called_once()


@pytest.mark.asyncio
async def test_main_handles_sqlite_error():
    """_main() should exit on sqlite3.OperationalError with database lock."""
    mock_client = AsyncMock()
    mock_client.start.side_effect = sqlite3.OperationalError("database is locked")

    with patch.object(main, "client", mock_client), \
         pytest.raises(SystemExit) as exc_info:
        await main._main()
    assert exc_info.value.code == 1


@pytest.mark.asyncio
async def test_main_handles_generic_error():
    """_main() should exit on generic exceptions."""
    mock_client = AsyncMock()
    mock_client.start.side_effect = RuntimeError("connection failed")

    with patch.object(main, "client", mock_client), \
         pytest.raises(SystemExit) as exc_info:
        await main._main()
    assert exc_info.value.code == 1


def test_main_sync_applies_nest_asyncio():
    """main() should call nest_asyncio.apply()."""
    with patch("main.nest_asyncio") as mock_nest, \
         patch("main.asyncio") as mock_asyncio:
        main.main()
        mock_nest.apply.assert_called_once()
        mock_asyncio.run.assert_called_once()
