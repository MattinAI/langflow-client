# tests/test_client.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx
from src.langflow_client import LangflowClient, Flow
from src.langflow_client.models import RequestOptions, LangflowClientOptions
from src.langflow_client.exceptions import LangflowError, LangflowRequestError

class TestLangflowClient:
    def test_init_default(self):
        """Test default client initialization."""
        client = LangflowClient()
        assert client.base_url == "http://localhost:7860"
        assert client.base_path == "/api/v1"
        assert client.api_key is None
        assert client.timeout == 30.0

    def test_init_with_base_url(self):
        """Test client initialization with custom base URL."""
        client = LangflowClient(base_url="http://my-langflow.com:7860")
        assert client.base_url == "http://my-langflow.com:7860"

    def test_init_with_api_key(self):
        """Test client initialization with API key."""
        client = LangflowClient(api_key="test-key")
        assert client.api_key == "test-key"

    def test_init_with_all_params(self):
        """Test client initialization with all parameters."""
        client = LangflowClient(
            base_url="http://my-langflow.com:7860",
            api_key="test-key", 
            timeout=60.0
        )
        assert client.base_url == "http://my-langflow.com:7860"
        assert client.api_key == "test-key"
        assert client.timeout == 60.0

    def test_init_with_opts(self):
        """Test initialization with LangflowClientOptions."""
        opts = LangflowClientOptions(base_url="http://test.com", api_key="key")
        client = LangflowClient(opts=opts)
        assert client.base_url == "http://test.com"

    def test_set_headers_combination(self):
        client = LangflowClient(api_key="test")
        headers = client._set_headers({"Custom": "value"})
        assert headers["x-api-key"] == "test"
        assert headers["Custom"] == "value"
        assert "User-Agent" in headers

    def test_headers_without_api_key(self):
        """Test header setting without API key."""
        client = LangflowClient()
        headers = client._set_headers()
        assert "User-Agent" in headers
        assert "x-api-key" not in headers

    def test_headers_with_api_key(self):
        """Test header setting with API key."""
        client = LangflowClient(api_key="test-key")
        headers = client._set_headers()
        assert headers["x-api-key"] == "test-key"

    def test_flow_creation(self):
        """Test flow creation."""
        client = LangflowClient()
        flow = client.flow("test-flow-id")
        
        assert isinstance(flow, Flow)
        assert flow.flow_id == "test-flow-id"
        assert flow.client is client

    @pytest.mark.asyncio
    async def test_request_timeout_error(self, httpx_mock):
        """Test timeout handling."""
        import httpx
        client = LangflowClient(timeout=0.001)
        
        # Mock timeout
        with patch('httpx.AsyncClient.request', side_effect=httpx.TimeoutException("Timeout")):
            with pytest.raises(LangflowRequestError) as exc:
                await client.request(RequestOptions("/test", "GET"))
            assert "Timeout" in str(exc.value)

    @pytest.mark.asyncio
    async def test_request_connection_error(self):
        """Test connection error handling."""
        import httpx
        client = LangflowClient()
        
        with patch('httpx.AsyncClient.request', side_effect=httpx.RequestError("Connection failed")):
            with pytest.raises(LangflowRequestError) as exc:
                await client.request(RequestOptions("/test", "GET"))
            assert "Request failed" in str(exc.value)

    @pytest.mark.asyncio
    async def test_request_success(self, httpx_mock):
        """Test successful API request."""
        client = LangflowClient()
        httpx_mock.add_response(
            method="GET",
            url="http://localhost:7860/api/v1/test",
            json={"result": "success"},
            status_code=200
        )
        
        result = await client.request(RequestOptions("/test", "GET"))
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_request_with_error(self, httpx_mock):
        """Test request with HTTP error."""
        client = LangflowClient()
        httpx_mock.add_response(
            method="GET",
            url="http://localhost:7860/api/v1/test",
            status_code=404,
            text="Not Found"
        )
                
        with pytest.raises(LangflowError) as exc_info:
            await client.request(RequestOptions("/test", "GET"))
        
        assert "404" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_with_json_error_fields(self, httpx_mock):
        """Test different JSON error field extractions."""
        client = LangflowClient()
        
        # Test 'detail' field
        httpx_mock.add_response(
            method="GET", url="http://localhost:7860/api/v1/test",
            status_code=400, json={"detail": "Invalid input"}
        )
        with pytest.raises(LangflowError) as exc_info:
            await client.request(RequestOptions("/test", "GET"))
        assert "Invalid input" in str(exc_info.value)
        
        # Test 'message' field
        httpx_mock.add_response(
            method="GET", url="http://localhost:7860/api/v1/test2", 
            status_code=400, json={"message": "Bad request"}
        )
        with pytest.raises(LangflowError):
            await client.request(RequestOptions("/test2", "GET"))

    @pytest.mark.asyncio  
    async def test_request_with_dict_error_response(self, httpx_mock):
        """Test dict/list error response conversion."""
        client = LangflowClient()
        
        # Test dict without standard fields
        httpx_mock.add_response(
            method="GET", url="http://localhost:7860/api/v1/test",
            status_code=400, json={"custom_field": "value"}
        )
        with pytest.raises(LangflowError) as exc_info:
            await client.request(RequestOptions("/test", "GET"))
        assert "custom_field" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_with_empty_response_after_json_failure(self, httpx_mock):
        """Test empty response handling when JSON parsing fails."""
        client = LangflowClient()
        httpx_mock.add_response(
            method="GET",
            url="http://localhost:7860/api/v1/test",
            status_code=200,
            text=""  # Empty response
        )
        
        with pytest.raises(LangflowError) as exc_info:
            await client.request(RequestOptions("/test", "GET"))
        assert "Empty response from server" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_with_text_response_after_json_failure(self, httpx_mock):
        """Test non-JSON text response handling."""
        client = LangflowClient()
        httpx_mock.add_response(
            method="GET",
            url="http://localhost:7860/api/v1/test",
            status_code=200,
            text="Plain text response"
        )
        
        result = await client.request(RequestOptions("/test", "GET"))
        assert result == "Plain text response"

    @pytest.mark.asyncio
    async def test_api_key_authentication_success(self, httpx_mock):
        """Test successful API key authentication."""
        client = LangflowClient(api_key="valid-api-key")
        
        httpx_mock.add_response(
            method="GET",
            url="http://localhost:7860/api/v1/test",
            json={"result": "authenticated"},
            status_code=200,
            match_headers={"x-api-key": "valid-api-key"}
        )
        
        result = await client.request(RequestOptions("/test", "GET"))
        assert result == {"result": "authenticated"} 

    @pytest.mark.asyncio  
    async def test_api_key_authentication_failure(self, httpx_mock):
        """Test API key authentication failure."""
        client = LangflowClient(api_key="invalid-api-key")
        
        httpx_mock.add_response(
            method="GET",
            url="http://localhost:7860/api/v1/test",
            json={"detail": "Invalid API key"},
            status_code=401
        )
        
        with pytest.raises(LangflowError) as exc_info:
            await client.request(RequestOptions("/test", "GET"))
        assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_missing_api_key_on_protected_endpoint(self, httpx_mock):
        """Test access to protected endpoint without API key."""
        client = LangflowClient()  # No API key
        
        httpx_mock.add_response(
            method="GET",
            url="http://localhost:7860/api/v1/protected",
            json={"detail": "API key required"},
            status_code=401
        )
        
        with pytest.raises(LangflowError) as exc_info:
            await client.request(RequestOptions("/protected", "GET"))
        assert "API key required" in str(exc_info.value)