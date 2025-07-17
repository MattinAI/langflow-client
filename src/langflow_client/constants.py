"""Constants for the Langflow client."""

from enum import Enum


class InputTypes(str, Enum):
    """Available input types for Langflow API."""
    CHAT = "chat"
    TEXT = "text"
    ANY = "any"


class OutputTypes(str, Enum):
    """Available output types for Langflow API."""
    CHAT = "chat"
    TEXT = "text"
    ANY = "any"