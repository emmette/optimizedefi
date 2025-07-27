"""Shared pytest fixtures and configuration."""

import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set test environment variables before importing app
os.environ["TESTING"] = "true"
os.environ["OPENROUTER_API_KEY"] = "test-api-key"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_llm():
    """Mock LLM for testing without API calls."""
    with patch("app.agents.base.ChatOpenAI") as mock:
        llm_instance = MagicMock()
        llm_instance.ainvoke.return_value = MagicMock(content="Test response")
        mock.return_value = llm_instance
        yield llm_instance


@pytest.fixture
def test_wallet_address():
    """Test wallet address."""
    return "0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7"


@pytest.fixture
def test_siwe_message():
    """Test SIWE message."""
    return {
        "domain": "localhost",
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7",
        "statement": "Sign in to OptimizeDeFi",
        "uri": "http://localhost:3000",
        "version": "1",
        "chain_id": 1,
        "nonce": "test-nonce-123",
        "issued_at": "2024-01-01T00:00:00.000Z"
    }


@pytest.fixture
def test_jwt_token():
    """Generate a test JWT token."""
    from app.core.auth import create_access_token
    return create_access_token(data={"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7"})


@pytest.fixture
def websocket_url():
    """WebSocket URL for testing."""
    return "/api/chat/ws/{client_id}"