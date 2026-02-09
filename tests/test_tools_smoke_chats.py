"""Smoke tests for chats, groups, media, and profile tools."""
import pytest


# ---------------------------------------------------------------------------
# Chats & Groups (20 tests)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_chat_smoke(patched_main):
    result = await patched_main.get_chat(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_list_chats_smoke(patched_main):
    result = await patched_main.list_chats(chat_type=None, limit=20)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_direct_chat_by_contact_smoke(patched_main):
    result = await patched_main.get_direct_chat_by_contact(contact_query="testuser")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_contact_chats_smoke(patched_main):
    result = await patched_main.get_contact_chats(contact_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_last_interaction_smoke(patched_main):
    result = await patched_main.get_last_interaction(contact_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_create_group_smoke(patched_main):
    result = await patched_main.create_group(title="Test Group", user_ids=[100, 200])
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_invite_to_group_smoke(patched_main):
    result = await patched_main.invite_to_group(group_id=100, user_ids=[200])
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_leave_chat_smoke(patched_main):
    result = await patched_main.leave_chat(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_participants_smoke(patched_main):
    result = await patched_main.get_participants(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_create_channel_smoke(patched_main):
    result = await patched_main.create_channel(title="Test Channel", about="", megagroup=False)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_edit_chat_title_smoke(patched_main):
    result = await patched_main.edit_chat_title(chat_id=100, title="New Title")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_edit_chat_photo_smoke(patched_main):
    result = await patched_main.edit_chat_photo(chat_id=100, file_path="/tmp/test.jpg")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_delete_chat_photo_smoke(patched_main):
    result = await patched_main.delete_chat_photo(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_subscribe_public_channel_smoke(patched_main):
    result = await patched_main.subscribe_public_channel(channel="test_channel")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_admins_smoke(patched_main):
    result = await patched_main.get_admins(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_banned_users_smoke(patched_main):
    result = await patched_main.get_banned_users(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_invite_link_smoke(patched_main):
    result = await patched_main.get_invite_link(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_join_chat_by_link_smoke(patched_main):
    result = await patched_main.join_chat_by_link(link="https://t.me/joinchat/abc")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_export_chat_invite_smoke(patched_main):
    result = await patched_main.export_chat_invite(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_import_chat_invite_smoke(patched_main):
    result = await patched_main.import_chat_invite(hash="abc123")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Media (5 tests)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_file_smoke(patched_main):
    result = await patched_main.send_file(chat_id=100, file_path="/tmp/test.txt", caption=None)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_download_media_smoke(patched_main):
    result = await patched_main.download_media(chat_id=100, message_id=1, file_path="/tmp/out.jpg")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_send_voice_smoke(patched_main):
    result = await patched_main.send_voice(chat_id=100, file_path="/tmp/voice.ogg")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_send_sticker_smoke(patched_main):
    result = await patched_main.send_sticker(chat_id=100, file_path="/tmp/sticker.webp")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_media_info_smoke(patched_main):
    result = await patched_main.get_media_info(chat_id=100, message_id=1)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# User & Profile (6 tests)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_me_smoke(patched_main):
    result = await patched_main.get_me()
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_update_profile_smoke(patched_main):
    result = await patched_main.update_profile(first_name="Test")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_set_profile_photo_smoke(patched_main):
    result = await patched_main.set_profile_photo(file_path="/tmp/photo.jpg")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_delete_profile_photo_smoke(patched_main):
    result = await patched_main.delete_profile_photo()
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_user_photos_smoke(patched_main):
    result = await patched_main.get_user_photos(user_id=100, limit=10)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_user_status_smoke(patched_main):
    result = await patched_main.get_user_status(user_id=100)
    assert isinstance(result, str)
