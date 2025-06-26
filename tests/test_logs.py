# tests/test_logs.py
import pytest
from src.langflow_client.logs import LogsAPI

class TestLogsAPI:
    @pytest.mark.asyncio
    async def test_fetch_basic(self, mock_langflow_client):
        """Test basic log fetching."""
        mock_langflow_client.request.return_value = [{"timestamp": 123, "message": "test"}]
        
        logs_api = LogsAPI(mock_langflow_client)
        result = await logs_api.fetch()
        
        mock_langflow_client.request.assert_called_once()
        call_args = mock_langflow_client.request.call_args[0][0]
        assert call_args.path == "/logs"
        assert call_args.method == "GET"

    @pytest.mark.asyncio
    async def test_fetch_with_timestamp(self, mock_langflow_client):
        """Test log fetching with timestamp."""
        logs_api = LogsAPI(mock_langflow_client)
        await logs_api.fetch(timestamp=1234567890)
        
        call_args = mock_langflow_client.request.call_args[0][0]
        assert "timestamp=1234567890" in call_args.path

    @pytest.mark.asyncio
    async def test_fetch_with_lines_after(self, mock_langflow_client):
        """Test log fetching with lines_after."""
        logs_api = LogsAPI(mock_langflow_client)
        await logs_api.fetch(lines_after=10)
        
        call_args = mock_langflow_client.request.call_args[0][0]
        assert "lines_after=10" in call_args.path

    @pytest.mark.asyncio
    async def test_fetch_with_multiple_params(self, mock_langflow_client):
        """Test log fetching with multiple parameters."""
        logs_api = LogsAPI(mock_langflow_client)
        await logs_api.fetch(
            timestamp=1234567890,
            lines_before=5,
            lines_after=10
        )
        
        call_args = mock_langflow_client.request.call_args[0][0]
        path = call_args.path
        assert "timestamp=1234567890" in path
        assert "lines_before=5" in path
        assert "lines_after=10" in path