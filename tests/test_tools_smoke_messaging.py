"""Smoke tests for messaging and contacts tools."""
import pytest


# ---------------------------------------------------------------------------
# Messaging (16 tests)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_chats_smoke(patched_main):
    result = await patched_main.get_chats(page=1, page_size=20)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_messages_smoke(patched_main):
    result = await patched_main.get_messages(chat_id=100, page=1, page_size=20)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_send_message_smoke(patched_main):
    result = await patched_main.send_message(chat_id=100, message="Hello test")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_list_messages_smoke(patched_main):
    result = await patched_main.list_messages(chat_id=100, limit=20)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_list_messages_with_search_smoke(patched_main):
    result = await patched_main.list_messages(chat_id=100, limit=10, search_query="hello")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_list_messages_with_dates_smoke(patched_main):
    result = await patched_main.list_messages(
        chat_id=100, limit=10, from_date="2026-01-01", to_date="2026-01-31"
    )
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_list_topics_smoke(patched_main):
    result = await patched_main.list_topics(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_history_smoke(patched_main):
    result = await patched_main.get_history(chat_id=100, limit=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_reply_to_message_smoke(patched_main):
    result = await patched_main.reply_to_message(chat_id=100, message_id=1, text="Reply text")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_edit_message_smoke(patched_main):
    result = await patched_main.edit_message(chat_id=100, message_id=1, new_text="Edited text")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_delete_message_smoke(patched_main):
    result = await patched_main.delete_message(chat_id=100, message_id=1)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_forward_message_smoke(patched_main):
    result = await patched_main.forward_message(from_chat_id=100, message_id=1, to_chat_id=200)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_pin_message_smoke(patched_main):
    result = await patched_main.pin_message(chat_id=100, message_id=1)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_unpin_message_smoke(patched_main):
    result = await patched_main.unpin_message(chat_id=100, message_id=1)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_mark_as_read_smoke(patched_main):
    result = await patched_main.mark_as_read(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_message_context_smoke(patched_main):
    result = await patched_main.get_message_context(chat_id=100, message_id=1, context_size=3)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_pinned_messages_smoke(patched_main):
    result = await patched_main.get_pinned_messages(chat_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_search_messages_smoke(patched_main):
    result = await patched_main.search_messages(chat_id=100, query="test", limit=20)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Contacts (10 tests)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_contacts_smoke(patched_main):
    result = await patched_main.list_contacts()
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_search_contacts_smoke(patched_main):
    result = await patched_main.search_contacts(query="Test")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_contact_ids_smoke(patched_main):
    result = await patched_main.get_contact_ids()
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_add_contact_smoke(patched_main):
    result = await patched_main.add_contact(phone="+1234567890", first_name="Test", last_name="User")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_delete_contact_smoke(patched_main):
    result = await patched_main.delete_contact(user_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_block_user_smoke(patched_main):
    result = await patched_main.block_user(user_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_unblock_user_smoke(patched_main):
    result = await patched_main.unblock_user(user_id=100)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_get_blocked_users_smoke(patched_main):
    result = await patched_main.get_blocked_users()
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_import_contacts_smoke(patched_main):
    result = await patched_main.import_contacts(
        contacts=[{"phone": "123", "first_name": "Test"}]
    )
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_export_contacts_smoke(patched_main):
    result = await patched_main.export_contacts()
    assert isinstance(result, str)
