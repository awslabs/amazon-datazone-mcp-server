"""Configuration module for SMUS Admin Agent."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the SMUS Admin Agent."""
    
    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.default_model = os.getenv("DEFAULT_MODEL", "claude-3-5-sonnet-20241022")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4096"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.1"))
        self.mcp_server_path = "."
    
    @property
    def is_configured(self) -> bool:
        """Check if the configuration is valid."""
        return bool(self.anthropic_api_key)
    
    def validate_api_key(self) -> None:
        """Validate that the API key is available. Raise error if not."""
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required. "
                "Please set it in your environment or .env file."
            )

    @property
    def is_mcp_configured(self) -> bool:
        """Check if the MCP server path is configured."""
        return bool(self.mcp_server_path)


# Global configuration instance
config = Config() 