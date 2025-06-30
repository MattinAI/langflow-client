"""Flow class for Langflow client."""

import httpx
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING

from .models import RequestOptions, Tweaks
from .constants import InputTypes, OutputTypes
from .exceptions import LangflowError, LangflowRequestError

if TYPE_CHECKING:
    from .client import LangflowClient


class FlowRequestOptions:
    """Options for running a flow."""
    def __init__(
        self,
        input_type: Optional[InputTypes] = None,
        output_type: Optional[OutputTypes] = None,
        session_id: Optional[str] = None,
        tweaks: Optional[Tweaks] = None,
    ):
        self.input_type = input_type
        self.output_type = output_type
        self.session_id = session_id
        self.tweaks = tweaks or Tweaks()


class Flow:
    """Represents a Langflow flow that can be executed."""
    
    def __init__(self, client: 'LangflowClient', flow_id: str, tweaks: Optional[Dict[str, Any]] = None):
        self.client = client
        self.flow_id = flow_id
        self.tweaks = tweaks or {}
    
    def tweak(self, **tweaks: Any) -> 'Flow':
        """
        Create a new Flow instance with tweaks applied.
        
        Args:
            **tweaks: Component tweaks to apply
            
        Returns:
            New Flow instance with tweaks
        """
        new_flow = Flow(self.client, self.flow_id)
        new_flow.tweaks = Tweaks(tweaks)
        return new_flow
    
    async def run(
        self, 
        input_value: Union[str, Dict[str, Any], None] = None,
        options: Optional[FlowRequestOptions] = None
    ) -> Any:
        """
        Run the flow with the given inputs.
        
        Args:
            inputs: Input text
            options: Optional request options
            
        Returns:
            Flow execution result or async generator for streaming
        """
        if options is None:
            options = FlowRequestOptions()
        
        # Combine instance tweaks with options tweaks
        combined_tweaks = {**self.tweaks, **options.tweaks}

        payload = {
            "input_value": input_value,
            "tweaks": combined_tweaks
        }
        
        if options.session_id:
            payload["session_id"] = options.session_id
        if options.input_type:
            payload["input_type"] = options.input_type.value
        if options.output_type:
            payload["output_type"] = options.output_type.value
            
        headers = {"Content-Type": "application/json", 
                   "Accept": "application/json"}
        
        request_options = RequestOptions(
            path=f"/run/{self.flow_id}",
            method="POST",
            body=payload,
            headers=headers
        )
        
        return await self.client.request(request_options)
    
    async def upload_file(self, file_path: str) -> Dict[str, str]:
        """
        Upload a file to be used with this flow.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            Dictionary with flowId and filePath
        """
        import aiofiles
        
        try:
            async with aiofiles.open(file_path, 'rb') as file:
                file_data = await file.read()
                
            files = {"file": (file_path.split('/')[-1], file_data)}
            
            url = f"{self.client.base_url}{self.client.base_path}/files/upload/{self.flow_id}"
            
            headers = {}
            if self.client.api_key:
                headers["x-api-key"] = self.client.api_key
            
            client_to_use = self.client.http_client or httpx.AsyncClient(timeout=self.client.timeout)
            
            try:
                if self.client.http_client:
                    response = await client_to_use.post(url, files=files, headers=headers)
                else:
                    async with client_to_use as client:
                        response = await client.post(url, files=files, headers=headers)
                
                if not response.is_success:
                    if response.status_code == 501:
                        raise LangflowError("File upload not supported by this Langflow instance", response)
                    raise LangflowError(f"Upload failed: {response.status_code} - {response.text}", response)
                
                result = response.json()
                return {
                    "flowId": self.flow_id,
                    "filePath": result.get("file_path", "")
                }
                
            except httpx.RequestError as e:
                raise LangflowRequestError(f"File upload failed: {str(e)}", e)
            
        except FileNotFoundError as e:
            raise LangflowError(f"File not found: {file_path}", None)
        except LangflowError:
            raise 
        except Exception as e:
            raise LangflowRequestError(f"File upload error: {str(e)}", e)
        