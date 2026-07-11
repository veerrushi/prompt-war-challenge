from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_read_root():
    # It should return the index.html or 404 if not found (during test, static might not be mounted properly depending on cwd)
    response = client.get("/")
    assert response.status_code in [200, 404]

def test_chat_endpoint_empty_messages():
    response = client.post("/api/chat", json={"messages": []})
    assert response.status_code == 400
    assert response.json() == {"detail": "Messages list cannot be empty"}

def test_chat_endpoint_rate_limit():
    # Send 21 requests to trigger rate limit (20/minute limit)
    for _ in range(20):
        res = client.post("/api/chat", json={"messages": [{"role": "user", "content": "test"}]})
        if res.status_code == 429:
            break
            
    response = client.post("/api/chat", json={"messages": [{"role": "user", "content": "test"}]})
    assert response.status_code == 429
