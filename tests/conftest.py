# tests/conftest.py
import pytest
from unittest.mock import AsyncMock

from src.langflow_client import LangflowClient
import os

# Test configuration
LANGFLOW_URL = os.getenv("LANGFLOW_TEST_URL", "http://localhost:7860")
LANGFLOW_API_KEY = os.getenv("LANGFLOW_TEST_API_KEY")  # Optional
TEST_FLOW_ID = os.getenv("LANGFLOW_TEST_FLOW_ID", "your-test-flow-id")

@pytest.fixture
def mock_langflow_client():
    """Shared mock client fixture."""
    client = AsyncMock()
    client.base_url = "http://localhost:7860"
    client.base_path = "/api/v1"
    client.api_key = "test-key"
    client.timeout = 30.0
    client.http_client = None
    return client

@pytest.fixture
def sample_flow_response():
    """Sample flow response for testing."""
    return {
        "outputs": [
            {
                "inputs": {"input": "Hello"},
                "outputs": {
                    "output": {
                        "message": "Hello! How can I help you today?",
                        "type": "text"
                    }
                }
            }
        ],
        "session_id": "test-session"
    }

@pytest.fixture
def integration_client():
    """Provide a client configured for integration tests."""
    return LangflowClient(
        base_url=LANGFLOW_URL,
        api_key=LANGFLOW_API_KEY
    )