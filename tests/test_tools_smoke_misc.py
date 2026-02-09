"""Smoke tests for search, reactions, privacy, misc, drafts, folders, and admin tools."""
import pytest


# ---------------------------------------------------------------------------
# Search (4 tests)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_public_chats_smoke(patched_main):
    result = await patched_main.search_public_chats(query="test")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_resolve_username_smoke(patched_main):
    result = await patched_main.resolve_username(username="test_user")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_recent_actions_smoke(patched_main):
    result = await patched_main.get_recent_actions(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_list_inline_buttons_smoke(patched_main):
    result = await patched_main.list_inline_buttons(chat_id=100, message_id=1)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Reactions (4 tests)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_reaction_smoke(patched_main):
    result = await patched_main.send_reaction(chat_id=100, message_id=1, emoji="\ud83d\udc4d")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_remove_reaction_smoke(patched_main):
    result = await patched_main.remove_reaction(chat_id=100, message_id=1)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_message_reactions_smoke(patched_main):
    result = await patched_main.get_message_reactions(chat_id=100, message_id=1)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_press_inline_button_smoke(patched_main):
    result = await patched_main.press_inline_button(chat_id=100, message_id=1, button_index=0)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Privacy (6 tests)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_privacy_settings_smoke(patched_main):
    result = await patched_main.get_privacy_settings()
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_set_privacy_settings_smoke(patched_main):
    result = await patched_main.set_privacy_settings(key="status")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_mute_chat_smoke(patched_main):
    result = await patched_main.mute_chat(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_unmute_chat_smoke(patched_main):
    result = await patched_main.unmute_chat(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_archive_chat_smoke(patched_main):
    result = await patched_main.archive_chat(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_unarchive_chat_smoke(patched_main):
    result = await patched_main.unarchive_chat(chat_id=100)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Misc (6 tests)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_sticker_sets_smoke(patched_main):
    result = await patched_main.get_sticker_sets()
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_gif_search_smoke(patched_main):
    result = await patched_main.get_gif_search(query="cat", limit=10)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_send_gif_smoke(patched_main):
    result = await patched_main.send_gif(chat_id=100, gif_id=12345)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_bot_info_smoke(patched_main):
    result = await patched_main.get_bot_info(bot_username="test_bot")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_set_bot_commands_smoke(patched_main):
    result = await patched_main.set_bot_commands(
        bot_username="test_bot",
        commands=[{"command": "start", "description": "Start"}],
    )
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_create_poll_smoke(patched_main):
    result = await patched_main.create_poll(
        chat_id=100, question="Test?", options=["Yes", "No"]
    )
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Drafts (3 tests)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_draft_smoke(patched_main):
    result = await patched_main.save_draft(chat_id=100, message="draft text")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_drafts_smoke(patched_main):
    result = await patched_main.get_drafts()
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_clear_draft_smoke(patched_main):
    result = await patched_main.clear_draft(chat_id=100)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Folders (7 tests)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_folders_smoke(patched_main):
    result = await patched_main.list_folders()
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_folder_smoke(patched_main):
    result = await patched_main.get_folder(folder_id=1)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_create_folder_smoke(patched_main):
    result = await patched_main.create_folder(title="Test Folder")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_add_chat_to_folder_smoke(patched_main):
    result = await patched_main.add_chat_to_folder(folder_id=1, chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_remove_chat_from_folder_smoke(patched_main):
    result = await patched_main.remove_chat_from_folder(folder_id=1, chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_delete_folder_smoke(patched_main):
    result = await patched_main.delete_folder(folder_id=1)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_reorder_folders_smoke(patched_main):
    result = await patched_main.reorder_folders(folder_ids=[1, 2])
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Admin (4 tests)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_promote_admin_smoke(patched_main):
    result = await patched_main.promote_admin(group_id=100, user_id=200)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_demote_admin_smoke(patched_main):
    result = await patched_main.demote_admin(group_id=100, user_id=200)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_ban_user_smoke(patched_main):
    result = await patched_main.ban_user(chat_id=100, user_id=200)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_unban_user_smoke(patched_main):
    result = await patched_main.unban_user(chat_id=100, user_id=200)
    assert isinstance(result, str)
