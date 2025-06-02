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

# def ask_claude_to_select_tools(user_input: str) -> list:
#     TOOL_KEYWORDS = {
#         "domain_management": ["domain"],
#         "project_management": ["project"],
#         "data_management": ["dataset", "schema", "data asset", "table", "column", "data"],
#         "glossary": ["glossary"],
#         "environment": ["environment", "infrastructure", "dev"]
#     }

#     selected_tools = set()

#     lower_input = user_input.lower()

#     for tool, keywords in TOOL_KEYWORDS.items():
#         for kw in keywords:
#             if re.search(rf"\b{re.escape(kw)}\b", lower_input):
#                 selected_tools.add(tool)
#                 break  # Avoid redundant checks

#     return list(selected_tools)

# configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# TOOLS_MAP = {
#     "domain_management": domain_management,
#     "project_management": project_management,
#     "data_management": data_management,
#     "glossary": glossary,
#     "environment": environment
# }

# def register_selected_tools(tool_names):
#     for name in tool_names:
#         if name in TOOLS_MAP:
#             TOOLS_MAP[name].register_tools(mcp)

# Register all tools from modules
domain_management.register_tools(mcp)
project_management.register_tools(mcp)
data_management.register_tools(mcp)
# glossary.register_tools(mcp)
environment.register_tools(mcp)

if __name__ == "__main__":
    try:
        # initial_input = sys.stdin.read()
        # input_data = json.loads(initial_input)
        # user_msg = input_data.get("input", "")

        # # Use Claude to decide which tools are relevant
        # selected_tools = ask_claude_to_select_tools(user_msg)

        # # Register only those tools
        # register_selected_tools(selected_tools)

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
        # initial_input = sys.stdin.read()
        # input_data = json.loads(initial_input)
        # user_msg = input_data.get("input", "")

        # # Use Claude to decide which tools are relevant
        # selected_tools = ask_claude_to_select_tools(user_msg)

        # # Register only those tools
        # register_selected_tools(selected_tools)
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
