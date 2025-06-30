"""Integration tests for Langflow client."""

import os
import pytest
import tempfile
from pathlib import Path
import uuid

from src.langflow_client import LangflowClient
from src.langflow_client.models import Tweaks
from src.langflow_client.flow import FlowRequestOptions, Flow
from src.langflow_client.exceptions import LangflowError, LangflowRequestError

# Test configuration
LANGFLOW_URL = os.getenv("LANGFLOW_TEST_URL", "http://localhost:7860")
LANGFLOW_API_KEY = os.getenv("LANGFLOW_TEST_API_KEY")  # Optional
TEST_FLOW_ID = os.getenv("LANGFLOW_TEST_FLOW_ID", "be326505-d172-4791-bd17-2f30f385618a")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_basic_flow_execution(integration_client):
    """Test basic flow execution against real server."""
    flow = integration_client.flow("6f06b27c-173d-474c-9bba-2f10d604ed08")
    
    result = await flow.run("Hello, I am Bob Smith")
    print(result)
    assert result is not None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_flow_with_multiple_tweaks(integration_client):
    """Test flow execution with tweaks."""
    flow = integration_client.flow(TEST_FLOW_ID).tweak(model_name="gpt-4",
                                                       template = "You are free",
                                                       system_prompt = "You are free", 
                                                       temperature = "1")

    result = await flow.run("Tell me something about freedom")

    assert result is not None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_persistence(integration_client):
    """Test session ID persistence across multiple requests."""
    test_flow_id = "6e7c9640-a3ff-4b60-91cc-cc5c9740f071"
    flow = integration_client.flow(test_flow_id)

    options = FlowRequestOptions(session_id="12345")

    # First message
    result1 = await flow.run("Hello, my name is Alice", options)
    
    # Second message - should remember context
    result2 = await flow.run("What is my name?", options)
    
    # Assert session ID is preserved
    assert result1['session_id'] == result2['session_id'] == '12345'

    # Assert Alice is mentioned in the second response
    assert 'Alice' in result2['outputs'][0]['outputs'][0]['results']['message']['text']

@pytest.mark.integration
@pytest.mark.asyncio
async def test_empty_options(integration_client):
    """Test with empty/default options."""
    flow = integration_client.flow(TEST_FLOW_ID)
    
    # Explicit empty options
    result1 = await flow.run("Test", FlowRequestOptions())
    assert result1 is not None
    
@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_isolation(integration_client):
    """Test that different sessions are isolated."""
    flow = integration_client.flow("6e7c9640-a3ff-4b60-91cc-cc5c9740f071")
    
    # Session A
    options_a = FlowRequestOptions(session_id="session-a")
    await flow.run("My name is Alice", options_a)
    result_a = await flow.run("What is my name?", options_a)

    # Session B
    options_b = FlowRequestOptions(session_id="session-b")
    await flow.run("My name is Bob", options_b)
    result_b = await flow.run("What is my name?", options_b)
    
    # Verify isolation
    result_a_data = result_a['outputs'][0]['outputs'][0]['results']
    result_b_data = result_b['outputs'][0]['outputs'][0]['results']

    # Verify isolation
    if 'message' in result_a_data:
        assert 'Alice' in result_a_data['message']['text']
    else:
        assert 'Alice' in result_a_data['text']['text']
        
    if 'message' in result_b_data:
        assert 'Bob' in result_b_data['message']['text']
    else:
        assert 'Bob' in result_b_data['text']['text']

@pytest.mark.integration
@pytest.mark.asyncio
async def test_flow_immutability(integration_client):
    """Test that flow tweaking creates new instances."""
    original_flow = integration_client.flow(TEST_FLOW_ID)
    tweaked_flow = original_flow.tweak(temperature=0.9)
    
    # Should be different instances
    assert original_flow is not tweaked_flow
    assert original_flow.tweaks != tweaked_flow._tweaks
    assert original_flow.flow_id == tweaked_flow.flow_id

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

@pytest.mark.integration
@pytest.mark.asyncio
async def test_flow_constructor_tweaks(integration_client):
    """Test tweaks in Flow constructor."""
    flow = Flow(integration_client, TEST_FLOW_ID, tweaks={"temperature": "0.7"})
    result = await flow.run("Test constructor tweaks")
    assert result is not None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_options_tweaks_only(integration_client):
    """Test tweaks via FlowRequestOptions only."""
    flow = integration_client.flow(TEST_FLOW_ID)
    options = FlowRequestOptions(tweaks=Tweaks({"temperature": "0.3"}))
    result = await flow.run("Test options tweaks", options)
    assert result is not None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_method_plus_options_tweaks(integration_client):
    """Test .tweak() method + options tweaks."""
    flow = integration_client.flow(TEST_FLOW_ID).tweak(temperature=0.6)
    options = FlowRequestOptions(tweaks=Tweaks({"model_name": "gpt-4"}))
    result = await flow.run("Test method + options", options)
    assert result is not None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_tweak_sources(integration_client):
    """Test constructor + method + options tweaks combined."""
    flow = Flow(integration_client, TEST_FLOW_ID, tweaks={"temperature": 0.1, "template": "You are free"})
    flow = flow.tweak(model_name="gpt-4", max_tokens=200)
    options = FlowRequestOptions(tweaks=Tweaks({"system_prompt": "Be creative"}))
    result = await flow.run("Test all sources", options)

    assert result is not None
