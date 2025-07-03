# tests/test_flow.py  
import pytest
from unittest.mock import AsyncMock, Mock, patch, mock_open
from src.langflow_client import Flow, InputTypes, OutputTypes, LangflowClient
from src.langflow_client.exceptions import LangflowError, LangflowRequestError

class TestFlow:
    def test_flow_init(self, mock_langflow_client):
        """Test flow initialization."""
        flow = Flow(mock_langflow_client, "test-flow")
        assert flow.client == mock_langflow_client
        assert flow.flow_id == "test-flow"

    def test_tweak_method(self, mock_langflow_client):
        """Test tweak method creates new flow instance."""
        flow = Flow(mock_langflow_client, "test-flow")
        tweaked = flow.tweak(OpenAI_1={"model": "gpt-4"})
        
        assert tweaked.flow_id == flow.flow_id
        assert tweaked.client == flow.client
        assert hasattr(tweaked, 'tweaks')
        assert tweaked.tweaks["OpenAI_1"]["model"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_run_basic(self, mock_langflow_client):
        """Test basic flow execution."""
        mock_langflow_client.request.return_value = {"result": "success"}
        
        flow = Flow(mock_langflow_client, "test-flow")
        result = await flow.run("hello")
        
        assert result == {"result": "success"}
        mock_langflow_client.request.assert_called_once()
        
        # Check the call arguments
        call_args = mock_langflow_client.request.call_args[0][0]
        assert call_args.path == "/run/test-flow"
        assert call_args.method == "POST"

    @pytest.mark.asyncio
    async def test_upload_file_with_http_client_501_error(self):
        """Test upload_file with pre-configured http_client and 501 error."""
        mock_response = AsyncMock()
        mock_response.is_success = False
        mock_response.status_code = 501
        mock_response.text = "Not Implemented"
        
        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        
        client = LangflowClient()
        client.http_client = mock_http_client
        flow = client.flow("test-flow")
        
        # Create proper async context manager mock
        mock_file = AsyncMock()
        mock_file.read.return_value = b'test content'
        
        async_cm = AsyncMock()
        async_cm.__aenter__ = AsyncMock(return_value=mock_file)
        async_cm.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiofiles.open', return_value=async_cm):
            with pytest.raises(LangflowError) as exc_info:
                await flow.upload_file("test.txt")
            
            assert "File upload not supported by this Langflow instance" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_success(self, mock_langflow_client, httpx_mock):
        """Test successful file upload."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:7860/api/v1/files/upload/test-flow",
            json={"file_path": "test-flow/123_test.jpg"},
            status_code=200
        )
        
        flow = Flow(mock_langflow_client, "test-flow")
        
        # Mock aiofiles
        import unittest.mock
        with unittest.mock.patch('aiofiles.open') as mock_open:
            mock_file = AsyncMock()
            mock_file.read.return_value = b"fake image data"
            mock_open.return_value.__aenter__.return_value = mock_file
            
            result = await flow.upload_file("test.jpg")
        
        assert result["flowId"] == "test-flow"
        assert result["filePath"] == "test-flow/123_test.jpg"
    
    @pytest.mark.asyncio
    async def test_upload_file_not_found(self):
        """Test upload_file with non-existent file."""
        client = LangflowClient()
        flow = client.flow("test-flow")
        
        with pytest.raises(LangflowError) as exc_info:
            await flow.upload_file("nonexistent.txt")
        assert "File not found: nonexistent.txt" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_general_exception(self):
        """Test upload_file with general exception during file operations."""
        client = LangflowClient()
        flow = client.flow("test-flow")
        
        # Mock aiofiles.open to raise a general exception
        with patch('aiofiles.open', side_effect=PermissionError("Access denied")):
            with pytest.raises(LangflowRequestError) as exc_info:
                await flow.upload_file("test.txt")
            assert "File upload error: Access denied" in str(exc_info.value)