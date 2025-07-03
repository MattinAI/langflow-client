"""Main Langflow client implementation."""

import httpx
import json
import logging
import platform
from typing import Dict, Any, Optional, AsyncGenerator

from .models import LangflowClientOptions, RequestOptions
from .exceptions import LangflowError, LangflowRequestError
from .flow import Flow

logger = logging.getLogger(__name__)


class LangflowClient:
    """
    Async client for interacting with Langflow API.
    """
    
    def __init__(
        self, 
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = 30.0,
        opts: Optional[LangflowClientOptions] = None
    ):
        """
        Initialize the Langflow client.
        
        Args:
            base_url: Base URL of the Langflow server
            api_key: API key for authentication
            timeout: Request timeout in seconds
            opts: Additional client options
        """
        if opts is None:
            opts = LangflowClientOptions()
            
        self.base_url = base_url or opts.base_url or "http://localhost:7860"
        self.base_path = "/api/v1"
        self.api_key = api_key or opts.api_key
        self.timeout = timeout or opts.timeout or 30.0
        self.default_headers = opts.default_headers or {}
        
        if "User-Agent" not in self.default_headers:
            self.default_headers["User-Agent"] = self._get_user_agent()
            
        self.http_client = opts.http_client
    
    def _get_user_agent(self) -> str:
        """Generate User-Agent string."""
        return f"langflow-python-client/1.0.0 ({platform.system()} {platform.machine()}) Python/{platform.python_version()}"
    
    def _set_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Combine default headers with request-specific headers."""
        combined_headers = {**self.default_headers}
        
        if headers:
            combined_headers.update(headers)
                
        if self.api_key:
            combined_headers["x-api-key"] = self.api_key
            
        return combined_headers
    
    def flow(self, flow_id: str) -> Flow:
        """
        Create a Flow instance for the given flow ID.
        
        Args:
            flow_id: Unique identifier for the flow
            tweaks: Optional tweaks to apply to the flow
            
        Returns:
            Flow instance
        """
        return Flow(self, flow_id)
        
    def _parse_error_response(self, response: httpx.Response) -> str:
        """Extract error message from response."""
        try:
            error_data = response.json()
            # Try different common error message fields
            for field in ['detail', 'message', 'error', 'error_description']:
                if field in error_data:
                    return str(error_data[field])
            
            # If it's a dict/list, convert to string
            if isinstance(error_data, (dict, list)):
                return str(error_data)
            
            return str(error_data)
        except (ValueError, TypeError):
            # Failed to parse JSON or not JSON response
            text = response.text.strip()
            return f"HTTP {response.status_code}: {text}" if text else f"HTTP {response.status_code}"
        
    async def request(self, options: RequestOptions) -> Any:
        """
        Make a request to the Langflow API.
        
        Args:
            options: Request configuration
            
        Returns:
            JSON response from the API
            
        Raises:
            LangflowError: For API errors
            LangflowRequestError: For request errors
        """
        path, method = options.path, options.method
        body = options.body
        headers = self._set_headers(options.headers)
        timeout = options.timeout or self.timeout
        url = f"{self.base_url}{self.base_path}{path}"
        
        client_to_use = self.http_client or httpx.AsyncClient(timeout=timeout)
        
        try:
            if self.http_client:
                response = await client_to_use.request(
                    method=method,
                    url=url,
                    json=body,
                    headers=headers
                )
            else:
                async with client_to_use as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        json=body,
                        headers=headers
                    )
            
            logger.debug(f"Response status: {response.status_code}")
            
            # Check for HTTP errors
            if not response.is_success:
                error_message = self._parse_error_response(response)
                raise LangflowError(error_message, response)

            # Parse successful response
            try:
                return response.json()
            except ValueError as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                response_text = response.text.strip()
                
                # Check if we got HTML instead of JSON (common when endpoint doesn't exist)
                if response_text.startswith("<!doctype html>") or response_text.startswith("<html"):
                    raise LangflowError("Received HTML page instead of API response - endpoint may not exist", response)
                
                # If we get an empty response on what should be a valid endpoint,
                # treat it as an error
                if not response_text:
                    raise LangflowError("Empty response from server", response)
                
                # Return text if JSON parsing fails but we have content
                return response_text
                            
        except LangflowError:
            # Re-raise our custom errors without modification
            raise
            
        except Exception as e:
            # Catch-all for unexpected errors
            error_str = str(e) or type(e).__name__
            error_msg = f"Request failed: {error_str}"
            logger.error(f"Unexpected error: {str(e)}: {url}", exc_info=True)
            raise LangflowRequestError(error_msg, e) from e
    