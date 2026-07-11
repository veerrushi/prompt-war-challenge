import pytest
from app.services.groq_service import GroqService, SYSTEM_PROMPT
from app.models.schemas import Message

class MockDelta:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content):
        self.delta = MockDelta(content)

class MockChunk:
    def __init__(self, content):
        self.choices = [MockChoice(content)] if content else []

class MockStream:
    def __init__(self, chunks):
        self.chunks = chunks
        
    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk

class MockCompletions:
    async def create(self, **kwargs):
        # Verify system prompt is included
        messages = kwargs.get("messages", [])
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == SYSTEM_PROMPT
        
        return MockStream([
            MockChunk("Hello"),
            MockChunk(" World"),
            MockChunk("!"),
            MockChunk(None)
        ])

class MockChat:
    def __init__(self):
        self.completions = MockCompletions()

class MockClient:
    def __init__(self):
        self.chat = MockChat()

@pytest.mark.asyncio
async def test_generate_chat_stream(monkeypatch):
    service = GroqService()
    # Replace the real client with our mock
    service.client = MockClient()
    
    messages = [Message(role="user", content="Hi")]
    
    chunks = []
    async for chunk in service.generate_chat_stream(messages):
        chunks.append(chunk)
        
    assert "".join(chunks) == "Hello World!"
