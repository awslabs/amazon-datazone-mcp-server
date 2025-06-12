import json
import logging
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

# Import tool modules
from .tools import (  # bedrock
    data_management,
    domain_management,
    environment,
    glossary,
    project_management,
)

# import boto3
# from botocore.config import Config


# initialize FastMCP server
mcp = FastMCP("datazone")
# bedrock.register_tools(mcp)


# configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add a handler to write to stderr
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.debug("DataZone MCP Server initializing...")

# bedrock_config = Config(
#     region_name="us-east-2",  # or your preferred region
#     retries={
#         'max_attempts': 5,
#         'mode': 'standard'
#     }
# )
# bedrock_runtime = boto3.client('bedrock-runtime', config=bedrock_config)

# def invoke_bedrock_model(prompt: str, model_id: str = "amazon.nova-lite-v1:0") -> str:
#     """
#     Invoke a Bedrock model with the given prompt.

#     Args:
#         prompt: The input prompt for the model
#         model_id: The Bedrock model ID (e.g., "anthropic.claude-3-5-sonnet-20241022-v2:0")

#     Returns:
#         The model's response as a string
#     """
#     if model_id.startswith("anthropic.claude"):
#         body = json.dumps({
#             "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
#             "max_tokens_to_sample": 2048,
#             "temperature": 0.5,
#             "top_p": 1,
#         })
#     else:
#         # Adjust for other model families (Amazon Titan, AI21, etc.)
#         body = json.dumps({"inputText": prompt})

#     response = bedrock_runtime.invoke_model(
#         body=body,
#         modelId=model_id,
#         accept='application/json',
#         contentType='application/json'
#     )

#     response_body = json.loads(response.get('body').read())

#     if model_id.startswith("anthropic.claude"):
#         return response_body.get("completion", "")
#     else:
#         return response_body.get("results", [{}])[0].get("outputText", "")


# Register all tools from modules
domain_management.register_tools(mcp)
project_management.register_tools(mcp)
data_management.register_tools(mcp)
glossary.register_tools(mcp)
environment.register_tools(mcp)


def main():
    """Entry point for console script."""
    try:
        # print("DEBUG: Server starting...", file=sys.stderr)
        # input_data = sys.stdin.read()
        # print(f"DEBUG: Received input: {input_data}", file=sys.stderr)

        # # Parse input
        # try:
        #     input_json = json.loads(input_data)
        #     user_input = input_json.get("input", "")
        # except json.JSONDecodeError:
        #     user_input = input_data.strip()

        # # Directly call the Bedrock tool
        # if user_input:
        #     print("DEBUG: Calling ask_bedrock directly", file=sys.stderr)
        #     response = bedrock.ask_bedrock(user_input)
        #     print(json.dumps({"response": response}))
        #     return

        # Fall back to MCP if no direct input
        mcp.run(transport="stdio")

        print("DEBUG: Server completed", file=sys.stderr)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Shutting down gracefully.", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        # Ensure we return a proper JSON response even in case of errors
        error_response = {
            "error": str(e),
            "type": type(e).__name__,
            "message": "MCP server encountered an error",
        }
        print(json.dumps(error_response))
        sys.exit(1)


if __name__ == "__main__":
    # try:
    #     mcp.run(transport='stdio')
    # except Exception as e:
    #     # Ensure we return a proper JSON response even in case of errors
    #     error_response = {
    #         "error": str(e),
    #         "type": type(e).__name__,
    #         "message": "MCP server encountered an error"
    #     }
    #     print(json.dumps(error_response))
    #     sys.exit(1)
    main()
