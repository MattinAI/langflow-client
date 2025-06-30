# Langflow Python Client

An async Python client library for interacting with Langflow API servers.

[![PyPI version](https://badge.fury.io/py/langflow-python-client.svg)](https://badge.fury.io/py/langflow-python-client)
[![Python Support](https://img.shields.io/pypi/pyversions/langflow-python-client.svg)](https://pypi.org/project/langflow-python-client/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

Features

- 🚀 Async/await support - Built with modern Python async patterns for high performance
- 🔐 Authentication - Secure API key authentication for protected Langflow instances
- 🎛️ Dynamic Tweaks - Modify flow behavior at runtime without changing flow definitions
- 📁 File Upload - Upload files directly to flows for document processing and analysis
- 📝 Type Safety - Full type annotation support with IDE autocomplete
- 🔧 Flexible Configuration - Support for different input/output types (text, chat)
- 🐍 Python 3.10+ - Compatible with modern Python versions

## Installation

```bash
pip install langflow-python-client
```

## Quick Start
### Basic Usage

```python
import asyncio
from langflow_client import LangflowClient, FlowRequestOptions
from langflow_client.constants import InputTypes, OutputTypes

async def main():
    # Initialize the client
    client = LangflowClient(
        base_url="http://localhost:7860"
    )
    
    # Get a flow instance
    flow = client.flow("your-flow-id")
    
    # Create request options
    options = FlowRequestOptions(
        input_type=InputTypes.TEXT,
        output_type=OutputTypes.TEXT,
        session_id="my-session"
    )
    
    # Run the flow
    result = await flow.run(
        "Hello, Langflow!",
        options=options
    )
    
    print(result)

# Run the async function
asyncio.run(main())
```

### Using Tweaks for Dynamic Configuration

Tweaks allow you to modify flow components at runtime without changing the flow definition:

```python
async def run_with_tweaks():
    client = LangflowClient(base_url="http://localhost:7860")
    
    # Create flow with component tweaks
    flow = client.flow("flow-id").tweak(**{
        "TextInput-ABC123": {
            "input_value": "Candidate CV content here..."
        },
        "OpenAI-DEF456": {
            "temperature": 0.7,
            "max_tokens": 500
        },
        "ChatOutput-GHI789": {
            "should_store_message": False
        }
    })
    
    # Run with options
    options = FlowRequestOptions(
        input_type=InputTypes.CHAT,
        output_type=OutputTypes.CHAT
    )
    
    result = await flow.run(options=options)
    return result
```

## Input and Output Types
The client supports different input and output types depending on your Langflow components:

| Type           | Description        | Use Case                              |
|----------------|--------------------|----------------------------------------|
| InputTypes.TEXT | Plain text input   | Simple text processing, document analysis |
| InputTypes.CHAT | Chat message format | Interactive chatbots, conversational AI  |
| OutputTypes.TEXT | Plain text output  | Clean text responses                     |
| OutputTypes.CHAT | Chat message format |  Interactive chatbots, conversational    |


### License
This project is licensed under the MIT License - see the LICENSE file for details.