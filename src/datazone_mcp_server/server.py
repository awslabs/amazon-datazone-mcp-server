from typing import Any
import json
import sys
import logging
from mcp.server.fastmcp import FastMCP

# Import tool modules
from .tools import (
    domain_management,
    project_management,
    data_management,
    glossary,
    environment
)

# initialize FastMCP server 
mcp = FastMCP("datazone")

# configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Register all tools from modules
domain_management.register_tools(mcp)
project_management.register_tools(mcp)
data_management.register_tools(mcp)
glossary.register_tools(mcp)
environment.register_tools(mcp)

if __name__ == "__main__":
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        # Ensure we return a proper JSON response even in case of errors
        error_response = {
            "error": str(e),
            "type": type(e).__name__,
            "message": "MCP server encountered an error"
        }
        print(json.dumps(error_response))
        sys.exit(1)

def main():
    """Entry point for console script."""
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        # Ensure we return a proper JSON response even in case of errors
        error_response = {
            "error": str(e),
            "type": type(e).__name__,
            "message": "MCP server encountered an error"
        }
        print(json.dumps(error_response))
        sys.exit(1)
