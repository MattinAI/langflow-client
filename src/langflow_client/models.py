"""Data models for the Langflow client."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import httpx


@dataclass
class LangflowClientOptions:
    """Options for configuring the Langflow client."""
    
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    timeout: Optional[float] = None
    default_headers: Optional[Dict[str, str]] = None
    http_client: Optional[httpx.AsyncClient] = None


@dataclass 
class RequestOptions:
    """Options for making requests to the Langflow API."""
    
    path: str
    method: str
    body: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[float] = None


class Tweaks(Dict[str, Any]):
    """
    Dictionary subclass for flow tweaks.
    
    Tweaks allow you to modify flow behavior by overriding component
    parameters without changing the flow definition.
    
    Example:
        tweaks = Tweaks({
            "OpenAI-1": {"model_name": "gpt-4"},
            "ChatInput-1": {"input_value": "Custom prompt"}
        })
    """
    pass
