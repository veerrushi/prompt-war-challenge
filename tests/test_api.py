"""
Integration tests for the FastAPI application routes.

Tests in this module use the shared ``client`` fixture from ``conftest.py``
and do NOT call the real Groq API – they only exercise routing, validation,
and rate-limiting behaviour.
"""

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Root / UI
# ---------------------------------------------------------------------------


def test_root_returns_ui_or_404(client: TestClient) -> None:
    """The root route serves index.html when the static dir is present,
    otherwise it returns a structured 404 response."""
    response = client.get("/")
    assert response.status_code in (
        200,
        404,
    ), f"Unexpected status {response.status_code} from GET /"


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


def test_health_check_returns_ok(client: TestClient) -> None:
    """The liveness probe should always return HTTP 200 with status=ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /api/chat – validation
# ---------------------------------------------------------------------------


def test_chat_rejects_empty_messages_list(client: TestClient) -> None:
    """An empty ``messages`` list must be rejected with HTTP 422 (schema-level)
    now that ``min_length=1`` is enforced on the Pydantic model."""
    response = client.post("/api/chat", json={"messages": []})
    # Pydantic min_length=1 raises a 422 Unprocessable Entity
    assert response.status_code in (400, 422)


def test_chat_rejects_invalid_role(client: TestClient) -> None:
    """A message with an unrecognised role must be rejected with HTTP 422."""
    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "robot", "content": "Hello"}]},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/chat – rate limiting
# ---------------------------------------------------------------------------


def test_chat_rate_limit_is_enforced(client: TestClient) -> None:
    """After 20 requests within a minute the server must return HTTP 429."""
    payload = {"messages": [{"role": "user", "content": "test"}]}

    for _ in range(20):
        res = client.post("/api/chat", json=payload)
        if res.status_code == 429:
            # Rate limit was hit before the 20th request – acceptable.
            return

    # The 21st request must be rate-limited.
    final = client.post("/api/chat", json=payload)
    assert final.status_code == 429, "Expected HTTP 429 after exceeding the rate limit."
