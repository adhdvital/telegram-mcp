"""Tests for error handling utilities."""

import pytest
from datetime import datetime

from main import log_and_format_error, ErrorCategory, json_serializer, ValidationError


# --- log_and_format_error tests ---


def test_error_with_category_prefix():
    result = log_and_format_error("get_chat", ValueError("test"), prefix=ErrorCategory.CHAT)
    assert isinstance(result, str)
    assert "CHAT-ERR" in result


def test_error_with_string_prefix():
    result = log_and_format_error("some_func", ValueError("test"), prefix="CUSTOM")
    assert isinstance(result, str)
    assert "CUSTOM-ERR" in result


def test_error_with_validation_prefix():
    result = log_and_format_error(
        "validate", ValidationError("bad id"), prefix="VALIDATION-001"
    )
    assert "VALIDATION-001" in result


def test_error_auto_derives_prefix():
    result = log_and_format_error("get_chat_info", ValueError("oops"))
    assert isinstance(result, str)
    assert "CHAT-ERR" in result


def test_error_with_user_message():
    result = log_and_format_error(
        "func", ValueError("technical"), user_message="Something went wrong"
    )
    assert result == "Something went wrong"


def test_error_with_no_prefix_match():
    result = log_and_format_error("unknown_func", ValueError("oops"))
    assert isinstance(result, str)
    assert "GEN-ERR" in result


def test_error_with_kwargs_context():
    result = log_and_format_error(
        "get_messages", ValueError("oops"), chat_id=100, page=1
    )
    assert isinstance(result, str)


# --- json_serializer tests ---


def test_json_serializer_datetime():
    dt = datetime(2026, 1, 1, 12, 0, 0)
    result = json_serializer(dt)
    assert "2026" in result


def test_json_serializer_bytes():
    result = json_serializer(b"hello")
    assert result == "hello"


def test_json_serializer_unknown_type():
    with pytest.raises(TypeError):
        json_serializer(set())


# --- ErrorCategory enum ---


def test_error_categories_exist():
    assert ErrorCategory.CHAT.value == "CHAT"
    assert ErrorCategory.MSG.value == "MSG"
    assert ErrorCategory.CONTACT.value == "CONTACT"
    assert ErrorCategory.GROUP.value == "GROUP"
    assert ErrorCategory.MEDIA.value == "MEDIA"
    assert ErrorCategory.PROFILE.value == "PROFILE"
    assert ErrorCategory.AUTH.value == "AUTH"
    assert ErrorCategory.ADMIN.value == "ADMIN"
    assert ErrorCategory.FOLDER.value == "FOLDER"
