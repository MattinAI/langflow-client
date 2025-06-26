"""Exception classes matching the TypeScript Langflow client."""

from typing import Optional
import httpx


class LangflowError(Exception):
    """HTTP error from the Langflow API (matches TypeScript LangflowError)."""
    
    def __init__(self, message: str, response: httpx.Response):
        super().__init__(message)
        self.cause = response
        self.response = response  


class LangflowRequestError(Exception):
    """Request error (network, timeout, etc.) (matches TypeScript LangflowRequestError)."""
    
    def __init__(self, message: str, error: Exception):
        super().__init__(message)
        self.cause = error