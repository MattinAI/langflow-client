# tests/test_exceptions.py
import httpx
from src.langflow_client.exceptions import LangflowError, LangflowRequestError

class TestExceptions:
    def test_langflow_error_basic(self):
        """Test basic LangflowError."""
        response = httpx.Response(404)  # Mock response
        error = LangflowError("test message", response)
        
        assert str(error) == "test message"
        assert error.cause == response
        assert error.response == response

    def test_langflow_error_with_response(self):
        """Test LangflowError with response."""
        response_mock = {"status": 400}
        error = LangflowError("test message", response_mock)
        assert error.response == response_mock

    def test_langflow_request_error(self):
        """Test LangflowRequestError with original error."""
        original = ConnectionError("Connection failed")
        error = LangflowRequestError("request failed", original)
        
        assert str(error) == "request failed"
        assert error.cause == original

    def test_langflow_request_error_with_original(self):
        """Test LangflowRequestError with original error."""
        original = ConnectionError("Connection failed")
        error = LangflowRequestError("request failed", original)
        assert error.cause == original

    def test_exception_inheritance(self):
        """Test exception inheritance."""
        assert issubclass(LangflowError, Exception)
        assert issubclass(LangflowRequestError, Exception)