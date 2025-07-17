# tests/test_constants.py
from src.langflow_client.constants import InputTypes, OutputTypes

class TestConstants:
    def test_input_types_values(self):
        """Test InputTypes enum values."""
        assert InputTypes.CHAT == "chat"
        assert InputTypes.TEXT == "text"
        assert InputTypes.ANY == "any"

    def test_output_types_values(self):
        """Test OutputTypes enum values."""
        assert OutputTypes.CHAT == "chat"
        assert OutputTypes.TEXT == "text" 
        assert OutputTypes.ANY == "any"

    def test_enum_inheritance(self):
        """Test that enums inherit from str."""
        assert isinstance(InputTypes.CHAT, str)
        assert isinstance(OutputTypes.TEXT, str)

    def test_enum_membership(self):
        """Test enum membership."""
        assert "chat" in [t.value for t in InputTypes]
        assert "text" in [t.value for t in OutputTypes]
