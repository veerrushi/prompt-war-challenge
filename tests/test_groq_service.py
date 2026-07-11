"""
Unit tests for GroqService.

All Groq API calls are mocked so the tests run without network access or
a valid API key, making them safe for CI environments.

Coverage targets:
- generate_chat_stream: happy path, multi-turn, empty chunks, APIError, generic Exception
- _build_messages: structure, ordering, system-prompt injection
- GroqService.__init__: model constant propagation
"""

import pytest

from app.models.schemas import Message
from app.services.groq_service import (
    MAX_TOKENS,
    MODEL_ID,
    SYSTEM_PROMPT,
    TEMPERATURE,
    GroqService,
)

# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


class _MockDelta:
    """Simulates ``chunk.choices[0].delta``."""

    def __init__(self, content: str | None) -> None:
        self.content = content


class _MockChoice:
    """Simulates ``chunk.choices[0]``."""

    def __init__(self, content: str | None) -> None:
        self.delta = _MockDelta(content)


class _MockChunk:
    """Simulates a single streamed chunk from the Groq API."""

    def __init__(self, content: str | None) -> None:
        self.choices = [_MockChoice(content)] if content is not None else []


class _MockStream:
    """Async-iterable that replays a fixed sequence of chunks."""

    def __init__(self, chunks: list[_MockChunk]) -> None:
        self._chunks = chunks

    async def __aiter__(self):
        for chunk in self._chunks:
            yield chunk


class _MockCompletions:
    """Replaces ``client.chat.completions`` with a deterministic mock.

    Captures kwargs so individual tests can inspect what was sent to the API.
    """

    def __init__(self, chunks: list[_MockChunk] | None = None) -> None:
        self.last_kwargs: dict = {}
        self._chunks = chunks or [
            _MockChunk("Hello"),
            _MockChunk(" World"),
            _MockChunk("!"),
            _MockChunk(None),
        ]

    async def create(self, **kwargs) -> _MockStream:
        self.last_kwargs = kwargs
        return _MockStream(self._chunks)


class _MockChat:
    def __init__(self, chunks: list[_MockChunk] | None = None) -> None:
        self.completions = _MockCompletions(chunks)


class _MockClient:
    def __init__(self, chunks: list[_MockChunk] | None = None) -> None:
        self.chat = _MockChat(chunks)


def _make_service(
    chunks: list[_MockChunk] | None = None,
) -> tuple[GroqService, _MockClient]:
    """Return a GroqService with an injected mock client."""
    service = GroqService()
    mock_client = _MockClient(chunks)
    service.client = mock_client
    return service, mock_client


# ---------------------------------------------------------------------------
# __init__ / constants
# ---------------------------------------------------------------------------


def test_service_uses_correct_model_id() -> None:
    """GroqService must be initialised with the canonical model constant."""
    service = GroqService()
    assert service.model == MODEL_ID


# ---------------------------------------------------------------------------
# _build_messages
# ---------------------------------------------------------------------------


def test_build_messages_prepends_system_prompt() -> None:
    """System prompt must always be the first element."""
    service, _ = _make_service()
    messages = [Message(role="user", content="Hello")]
    result = service._build_messages(messages)

    assert result[0] == {"role": "system", "content": SYSTEM_PROMPT}


def test_build_messages_preserves_conversation_order() -> None:
    """User and assistant messages must appear after the system prompt in order."""
    service, _ = _make_service()
    messages = [
        Message(role="user", content="First"),
        Message(role="assistant", content="Second"),
        Message(role="user", content="Third"),
    ]
    result = service._build_messages(messages)

    assert len(result) == 4  # system + 3 conversation messages
    assert result[1] == {"role": "user", "content": "First"}
    assert result[2] == {"role": "assistant", "content": "Second"}
    assert result[3] == {"role": "user", "content": "Third"}


def test_build_messages_maps_role_and_content() -> None:
    """Each message dict must contain exactly the role and content fields."""
    service, _ = _make_service()
    msg = Message(role="user", content="Test message")
    result = service._build_messages([msg])

    assert result[1]["role"] == "user"
    assert result[1]["content"] == "Test message"


# ---------------------------------------------------------------------------
# generate_chat_stream – happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_yields_all_non_empty_tokens() -> None:
    """All non-None, non-empty chunks from the API must be yielded."""
    service, _ = _make_service()
    chunks = [
        c
        async for c in service.generate_chat_stream(
            [Message(role="user", content="Hi")]
        )
    ]
    assert "".join(chunks) == "Hello World!"


@pytest.mark.asyncio
async def test_stream_skips_empty_choices() -> None:
    """Chunks with an empty ``choices`` list must be silently skipped."""
    service, _ = _make_service(
        chunks=[
            _MockChunk(None),  # empty choices list
            _MockChunk("A"),
            _MockChunk(None),
            _MockChunk("B"),
        ]
    )
    chunks = [
        c
        async for c in service.generate_chat_stream(
            [Message(role="user", content="test")]
        )
    ]
    assert "".join(chunks) == "AB"


@pytest.mark.asyncio
async def test_stream_passes_correct_model_and_params() -> None:
    """The API call must use MODEL_ID, TEMPERATURE, and MAX_TOKENS constants."""
    service, mock_client = _make_service()
    _ = [
        c
        async for c in service.generate_chat_stream(
            [Message(role="user", content="check params")]
        )
    ]
    kwargs = mock_client.chat.completions.last_kwargs
    assert kwargs["model"] == MODEL_ID
    assert kwargs["temperature"] == TEMPERATURE
    assert kwargs["max_tokens"] == MAX_TOKENS
    assert kwargs["stream"] is True


@pytest.mark.asyncio
async def test_stream_sends_system_prompt_as_first_message() -> None:
    """The system prompt must be the first message in the API payload."""
    service, mock_client = _make_service()
    _ = [
        c
        async for c in service.generate_chat_stream(
            [Message(role="user", content="Where do I evacuate?")]
        )
    ]
    first_msg = mock_client.chat.completions.last_kwargs["messages"][0]
    assert first_msg["role"] == "system"
    assert first_msg["content"] == SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_stream_multi_turn_conversation() -> None:
    """A multi-turn conversation history must be forwarded to the API intact."""
    service, mock_client = _make_service()
    messages = [
        Message(role="user", content="Is it safe to travel?"),
        Message(role="assistant", content="It depends on your location."),
        Message(role="user", content="I'm in Mumbai."),
    ]
    _ = [c async for c in service.generate_chat_stream(messages)]
    sent = mock_client.chat.completions.last_kwargs["messages"]
    # system + 3 turns = 4 messages
    assert len(sent) == 4
    assert sent[-1]["content"] == "I'm in Mumbai."


@pytest.mark.asyncio
async def test_stream_with_special_characters_in_content() -> None:
    """Messages containing special characters must be forwarded without modification."""
    service, mock_client = _make_service()
    special = "Hello! <>&\"' こんにちは 🌧️"
    _ = [
        c
        async for c in service.generate_chat_stream(
            [Message(role="user", content=special)]
        )
    ]
    sent_content = mock_client.chat.completions.last_kwargs["messages"][1]["content"]
    assert sent_content == special


# ---------------------------------------------------------------------------
# generate_chat_stream – error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_handles_groq_api_error(monkeypatch) -> None:
    """A Groq ``APIError`` must be caught and yield a user-friendly message."""
    from groq import APIError

    async def _raise_api_error(**kwargs):
        raise APIError("rate_limit_exceeded", response=None, body=None)

    service, mock_client = _make_service()
    monkeypatch.setattr(mock_client.chat.completions, "create", _raise_api_error)

    chunks = [
        c
        async for c in service.generate_chat_stream(
            [Message(role="user", content="test")]
        )
    ]
    combined = "".join(chunks)
    assert "⚠️" in combined
    assert len(combined) > 0  # must yield something, not be silent


@pytest.mark.asyncio
async def test_stream_handles_unexpected_exception(monkeypatch) -> None:
    """Any unexpected exception must be caught and yield a user-friendly message."""

    async def _raise_runtime_error(**kwargs):
        raise RuntimeError("Simulated unexpected failure")

    service, mock_client = _make_service()
    monkeypatch.setattr(mock_client.chat.completions, "create", _raise_runtime_error)

    chunks = [
        c
        async for c in service.generate_chat_stream(
            [Message(role="user", content="test")]
        )
    ]
    combined = "".join(chunks)
    assert "⚠️" in combined
    assert "unexpected" in combined.lower()


@pytest.mark.asyncio
async def test_stream_yields_nothing_for_all_empty_chunks() -> None:
    """If all chunks have no content, the generator should yield nothing."""
    service, _ = _make_service(
        chunks=[
            _MockChunk(None),
            _MockChunk(None),
        ]
    )
    chunks = [
        c
        async for c in service.generate_chat_stream(
            [Message(role="user", content="silent test")]
        )
    ]
    assert chunks == []
