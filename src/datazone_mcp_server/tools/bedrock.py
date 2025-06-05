from typing import Any, Dict
# from mcp import tool
import sys

def tool(func):
    func._is_tool = True
    return func

@tool
def ask_bedrock(prompt: str, model_id: str = "amazon.nova-lite-v1:0") -> str:
    """
    Ask a question to an Amazon Bedrock model and get the response.
    
    Args:
        prompt: The question or prompt to send to the model
        model_id: The Bedrock model ID to use (default: anthropic.claude-3-5-sonnet-20241022-v2:0)
    
    Returns:
        The model's response
    """
    print(f"heyy", file=sys.stderr)
    from server import invoke_bedrock_model  # Import from your server file
    print(f"DEBUG: ask_bedrock called with: {prompt}", file=sys.stderr)
    result = invoke_bedrock_model(prompt, model_id)
    print(f"DEBUG: Bedrock response: {result}", file=sys.stderr)
    return result

# Add this function to register tools with MCP
def register_tools(mcp_server: Any) -> None:
    """Register all tools in this module with the MCP server"""
    mcp_server.add_tool(ask_bedrock)