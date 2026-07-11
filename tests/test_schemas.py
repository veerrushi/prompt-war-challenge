"""
Unit tests for Pydantic request/response schemas.

These tests exercise the validation logic defined in ``app.models.schemas``
without starting the FastAPI server, making them fast and isolated.
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import ChatRequest, Message


# ---------------------------------------------------------------------------
# Message model
# ---------------------------------------------------------------------------


class TestMessage:
    """Validation tests for the ``Message`` schema."""

    def test_valid_user_message(self) -> None:
        """A well-formed user message must be accepted without errors."""
        msg = Message(role="user", content="What supplies do I need?")
        assert msg.role == "user"
        assert msg.content == "What supplies do I need?"

    def test_valid_assistant_message(self) -> None:
        """The 'assistant' role must be accepted."""
        msg = Message(role="assistant", content="You need water and a first-aid kit.")
        assert msg.role == "assistant"

    def test_valid_system_message(self) -> None:
        """The 'system' role must be accepted."""
        msg = Message(role="system", content="You are a helpful assistant.")
        assert msg.role == "system"

    def test_invalid_role_raises_validation_error(self) -> None:
        """An unrecognised role must raise a ``ValidationError``."""
        with pytest.raises(ValidationError) as exc_info:
            Message(role="robot", content="Hello")
        assert "role" in str(exc_info.value)

    def test_empty_content_raises_validation_error(self) -> None:
        """An empty content string must be rejected (``min_length=1``)."""
        with pytest.raises(ValidationError) as exc_info:
            Message(role="user", content="")
        assert "content" in str(exc_info.value)

    def test_missing_role_raises_validation_error(self) -> None:
        """Omitting the required ``role`` field must raise a ``ValidationError``."""
        with pytest.raises(ValidationError):
            Message(content="no role provided")  # type: ignore[call-arg]

    def test_missing_content_raises_validation_error(self) -> None:
        """Omitting the required ``content`` field must raise a ``ValidationError``."""
        with pytest.raises(ValidationError):
            Message(role="user")  # type: ignore[call-arg]

    def test_content_with_special_characters(self) -> None:
        """Content containing special / unicode characters must be accepted."""
        content = "Monsoon alert! ⛈️ Evacuate now – 洪水警告"
        msg = Message(role="user", content=content)
        assert msg.content == content

    def test_long_content_is_accepted(self) -> None:
        """Very long content strings must not be rejected."""
        long_content = "A" * 10_000
        msg = Message(role="user", content=long_content)
        assert len(msg.content) == 10_000


# ---------------------------------------------------------------------------
# ChatRequest model
# ---------------------------------------------------------------------------


class TestChatRequest:
    """Validation tests for the ``ChatRequest`` schema."""

    def test_valid_single_message_request(self) -> None:
        """A single-message payload must be accepted."""
        req = ChatRequest(messages=[{"role": "user", "content": "Hello"}])
        assert len(req.messages) == 1

    def test_valid_multi_turn_request(self) -> None:
        """Multiple alternating roles must all be accepted."""
        req = ChatRequest(messages=[
            {"role": "user", "content": "Is it safe?"},
            {"role": "assistant", "content": "Check local alerts."},
            {"role": "user", "content": "I'm in Chennai."},
        ])
        assert len(req.messages) == 3

    def test_empty_messages_raises_validation_error(self) -> None:
        """An empty ``messages`` list must be rejected (``min_length=1``)."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(messages=[])
        assert "messages" in str(exc_info.value)

    def test_missing_messages_field_raises_validation_error(self) -> None:
        """Omitting ``messages`` entirely must raise a ``ValidationError``."""
        with pytest.raises(ValidationError):
            ChatRequest()  # type: ignore[call-arg]

    def test_invalid_role_inside_request_raises_validation_error(self) -> None:
        """A message with an invalid role inside a ChatRequest must be rejected."""
        with pytest.raises(ValidationError):
            ChatRequest(messages=[{"role": "bot", "content": "Hi"}])

    def test_messages_are_message_instances(self) -> None:
        """Parsed messages must be ``Message`` model instances."""
        req = ChatRequest(messages=[{"role": "user", "content": "Ready?"}])
        assert isinstance(req.messages[0], Message)

    def test_json_schema_example_is_valid(self) -> None:
        """The built-in schema example must itself pass validation."""
        example = ChatRequest.model_config["json_schema_extra"]["example"]
        req = ChatRequest(**example)
        assert req.messages[0].role == "user"
