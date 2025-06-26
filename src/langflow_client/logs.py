"""Logs API for Langflow client."""

from typing import Dict, Any, Optional, List, TYPE_CHECKING

from .models import RequestOptions

if TYPE_CHECKING:
    from .client import LangflowClient


class LogsAPI:
    """API for fetching Langflow logs."""
    
    def __init__(self, client: 'LangflowClient'):
        self.client = client
    
    async def fetch(
        self,
        timestamp: Optional[int] = None,
        lines_before: Optional[int] = None,
        lines_after: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch logs from the Langflow instance.
        
        Args:
            timestamp: Unix timestamp to filter logs
            lines_before: Number of lines before timestamp
            lines_after: Number of lines after timestamp
            
        Returns:
            List of log entries
        """
        params = {}
        if timestamp:
            params["timestamp"] = timestamp
        if lines_before:
            params["lines_before"] = lines_before
        if lines_after:
            params["lines_after"] = lines_after
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        path = f"/logs?{query_string}" if query_string else "/logs"
        
        request_options = RequestOptions(
            path=path,
            method="GET"
        )
        
        return await self.client.request(request_options)