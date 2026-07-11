"""
Shared pytest fixtures for the RainReady AI test suite.

Fixtures defined here are automatically available to all test modules
without requiring an explicit import.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Return a module-scoped FastAPI test client.

    Using ``scope="module"`` means the app is only instantiated once per
    test module, which speeds up the suite significantly.
    """
    return TestClient(app)
