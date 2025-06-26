"""Integration tests for Langflow client."""

import os
import pytest
import tempfile
from pathlib import Path

from src.langflow_client import LangflowClient
from src.langflow_client.flow import RunOptions
from src.langflow_client.exceptions import LangflowError, LangflowRequestError

# Test configuration
LANGFLOW_URL = os.getenv("LANGFLOW_TEST_URL", "http://localhost:7860")
LANGFLOW_API_KEY = os.getenv("LANGFLOW_TEST_API_KEY")  # Optional
TEST_FLOW_ID = os.getenv("LANGFLOW_TEST_FLOW_ID", "1248fa1c-29b7-46b9-bd44-e03f9d8ad02e")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_basic_flow_execution(integration_client):
    """Test basic flow execution against real server."""
    flow = integration_client.flow(TEST_FLOW_ID)
    
    result = await flow.run("Hello, integration test!")

    assert result is not None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_flow_with_tweaks(integration_client):
    """Test flow execution with tweaks."""
    flow = integration_client.flow(TEST_FLOW_ID).tweak(model_name="gpt-4",
                                                       template = "You are free",
                                                       system_prompt = "You are free", 
                                                       temperature = "1")

    result = await flow.run("Hello how are you")

    assert result is not None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_file_upload_integration(integration_client):
    """Test file upload to real server."""
    flow = integration_client.flow(TEST_FLOW_ID)
    
    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Integration test file content")
        temp_file = f.name
    
    try:
        result = await flow.upload_file(temp_file)
        assert "flowId" in result
        assert "filePath" in result
        assert result["flowId"] == TEST_FLOW_ID
    finally:
        Path(temp_file).unlink()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_nonexistent_flow_error(integration_client):
    """Test error handling for non-existent flow."""
    # Use a clearly non-existent flow ID
    nonexistent_flow_id = "definitely-does-not-exist-12345"
    flow = integration_client.flow(nonexistent_flow_id)
    
    try:
        result = await flow.run("test")
        
        # If we get a result, check if it's an error disguised as success
        if result is None or result == "" or result == {}:
            pytest.fail("Got empty result instead of proper error for non-existent flow")
        
        # If we get a string result, check if it contains error info
        if isinstance(result, str) and ("error" in result.lower() or "not found" in result.lower()):
            pytest.fail(f"Got error as string result instead of exception: {result}")
            
        # If we get here with a real result, the flow might actually exist
        pytest.fail(f"Expected error for non-existent flow but got result: {result}")
        
    except (LangflowError, LangflowRequestError) as e:
        # This is what we expect - some kind of error
        error_msg = str(e).lower()
        
        # Check that the error message is meaningful
        assert (
            nonexistent_flow_id in str(e) or
            "not found" in error_msg or
            "404" in error_msg or
            "does not exist" in error_msg or
            "empty response" in error_msg or
            "html page instead of api response" in error_msg or
            "endpoint may not exist" in error_msg
        ), f"Error message doesn't indicate flow not found: {e}"
        
        print(f"✓ Got expected error: {type(e).__name__}: {e}")
        
    except Exception as e:
        pytest.fail(f"Got unexpected error type {type(e).__name__}: {e}")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_client_timeout():
    """Test timeout handling."""
    # Create client with very short timeout
    timeout_client = LangflowClient(
        base_url=LANGFLOW_URL,
        timeout=0.001
    )
    flow = timeout_client.flow(TEST_FLOW_ID)
    
    with pytest.raises(LangflowRequestError) as exc_info:
        await flow.run("test")
    
    assert "ConnectTimeout" in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.asyncio 
async def test_connection_error():
    """Test connection error handling."""
    client = LangflowClient(base_url="http://localhost:9999")
    flow = client.flow("any-flow")
    
    with pytest.raises(LangflowRequestError):
        await flow.run("test")
