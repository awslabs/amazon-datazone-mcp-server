import json
import logging
import sys
import os
import boto3
from typing import Any, Dict, Callable
import inspect

# Import the real MCP tools
from mcp.server.fastmcp import FastMCP
from .tools import domain_management, data_management, project_management, environment, glossary

# configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def initialize_aws_session():
    """Initialize AWS session with proper credential handling (no credential exposure)"""
    try:
        # Check for local development environment using generic environment variable
        # Use MCP_LOCAL_DEV=true to indicate local development instead of hardcoded key patterns
        is_local_dev = os.environ.get('MCP_LOCAL_DEV', '').lower() == 'true'
        
        if (is_local_dev and 
            os.environ.get('AWS_ACCESS_KEY_ID') and
            os.environ.get('AWS_SECRET_ACCESS_KEY') and
            os.environ.get('AWS_SESSION_TOKEN')):
            logger.info("Using AWS credentials from environment variables (local development)")
            session = boto3.Session(
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                aws_session_token=os.environ.get('AWS_SESSION_TOKEN'),
                region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
            )
            # Get account ID dynamically from STS
            try:
                sts_client = session.client('sts')
                account_id = sts_client.get_caller_identity()['Account']
                logger.info(f"Retrieved account ID from STS: {account_id}")
                return session, account_id
            except Exception as e:
                logger.warning(f"Could not retrieve account ID from STS: {e}")
                return session, os.environ.get('AWS_ACCOUNT_ID', 'unknown')
        
        # For AWS deployment, retrieve from Secrets Manager
        logger.info("Running in AWS environment - retrieving credentials from Secrets Manager...")
        secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
        
        secret_name = 'smus-ai/dev/mcp-aws-credentials'
        logger.info(f"Retrieving credentials from secret: {secret_name}")
        
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_value = json.loads(response['SecretString'])
        
        logger.info(f"Successfully retrieved credentials from Secrets Manager for account: {secret_value.get('ACCOUNT_ID', 'unknown')}")
        session = boto3.Session(
            aws_access_key_id=secret_value['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=secret_value['AWS_SECRET_ACCESS_KEY'],
            aws_session_token=secret_value['AWS_SESSION_TOKEN'],
            region_name=secret_value['AWS_DEFAULT_REGION']
        )
        return session, secret_value.get('ACCOUNT_ID', 'unknown')
        
    except Exception as e:
        logger.error(f"Failed to retrieve credentials from Secrets Manager: {e}")
        logger.warning("Falling back to default AWS credentials")
        # Try to get account ID from default session
        try:
            default_session = boto3.Session()
            sts_client = default_session.client('sts')
            account_id = sts_client.get_caller_identity()['Account']
            logger.info(f"Retrieved account ID from default credentials: {account_id}")
            return default_session, account_id
        except Exception as sts_e:
            logger.warning(f"Could not retrieve account ID from default credentials: {sts_e}")
            return boto3.Session(), os.environ.get('AWS_ACCOUNT_ID', 'unknown')

def create_mcp_server():
    """Create MCP server with real DataZone tools"""
    # Initialize AWS session securely
    session, account_id = initialize_aws_session()
    
    # Initialize FastMCP server
    mcp = FastMCP("datazone")
    
    # Initialize boto3 client with session
    try:
        datazone_client = session.client('datazone')
        logger.info(f"Successfully initialized DataZone client for account: {account_id}")
        
        # Verify credentials with STS get_caller_identity
        try:
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            actual_account = identity.get('Account', 'unknown')
            user_arn = identity.get('Arn', 'unknown')
            logger.info(f"STS VERIFICATION SUCCESS - DataZone MCP connected to AWS Account: {actual_account}")
            logger.info(f"STS Identity ARN: {user_arn}")
            
            # Log warning if account mismatch
            if actual_account != account_id and account_id != 'unknown':
                logger.warning(f"ACCOUNT MISMATCH - Expected: {account_id}, Actual: {actual_account}")
            else:
                logger.info(f"ACCOUNT MATCH CONFIRMED - Using correct account: {actual_account}")
                    
        except Exception as sts_error:
            logger.error(f"STS VERIFICATION FAILED - Cannot verify AWS credentials: {sts_error}")
                
    except Exception as e:
        logger.error(f"Failed to initialize DataZone client: {str(e)}")
        # Don't raise - allow server to start without credentials for testing
        datazone_client = None
    
    # Register all the real tools
    domain_management.register_tools(mcp)
    data_management.register_tools(mcp)
    project_management.register_tools(mcp)
    environment.register_tools(mcp)
    glossary.register_tools(mcp)
    
    return mcp

def create_http_app():
    """Create FastAPI app with real MCP tools for HTTP transport"""
    try:
        from fastapi import FastAPI, Request, Response
        from fastapi.responses import JSONResponse
        
        # Create the MCP server with real tools
        mcp = create_mcp_server()
        
        app = FastAPI(
            title="DataZone MCP Server",
            description="MCP server for AWS DataZone service",
            version="1.0.0"
        )
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint for ALB"""
            # Get the actual tool count from FastMCP's tool manager
            tool_count = len(mcp._tool_manager._tools)
            return {
                "status": "healthy",
                "service": "datazone-mcp-server",
                "version": "1.0.0",
                "transport": "http",
                "tools_count": tool_count
            }
        
        @app.get("/")
        def root():
            """Root endpoint with service info"""
            # Get actual tools from FastMCP's tool manager
            tools_available = list(mcp._tool_manager._tools.keys())
            return {
                "service": "DataZone MCP Server",
                "status": "running",
                "transport": "http",
                "endpoints": ["/health", "/mcp/datazone"],
                "tools_available": tools_available
            }
        
        @app.get("/mcp/datazone")
        def mcp_root():
            """MCP root endpoint"""
            return {
                "jsonrpc": "2.0",
                "method": "initialize",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "datazone-mcp-server",
                        "version": "1.0.0"
                    }
                }
            }
        
        @app.post("/mcp/datazone")
        async def mcp_endpoint(request: Request):
            """MCP JSON-RPC endpoint using real tools"""
            try:
                # Parse the request body
                request_data = await request.json()
                method = request_data.get("method")
                params = request_data.get("params", {})
                request_id = request_data.get("id")
                
                if method == "tools/list":
                    # Get actual tools from FastMCP's tool manager
                    tools = []
                    for tool_name, tool_obj in mcp._tool_manager._tools.items():
                        # Get tool info from the MCP tool object
                        try:
                            # Use the correct attributes from FastMCP Tool object
                            input_schema = tool_obj.model_json_schema() if hasattr(tool_obj, 'model_json_schema') else {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                            
                            tool_info = {
                                "name": tool_name,
                                "description": tool_obj.description or f"DataZone tool: {tool_name}",
                                "inputSchema": input_schema
                            }
                        except Exception as e:
                            # Fallback if schema generation fails
                            tool_info = {
                                "name": tool_name,
                                "description": tool_obj.description or f"DataZone tool: {tool_name}",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            }
                        tools.append(tool_info)
                    
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "tools": tools
                        }
                    }
                    
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    if tool_name in mcp._tool_manager._tools:
                        try:
                            # Call the tool using FastMCP's call_tool method
                            result = await mcp.call_tool(tool_name, arguments)
                            
                            # Format the result for MCP
                            if isinstance(result, dict) or isinstance(result, list):
                                result_text = json.dumps(result, indent=2, default=str)
                            else:
                                result_text = str(result)
                            
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": result_text
                                        }
                                    ]
                                }
                            }
                        except Exception as e:
                            logger.error(f"Error calling tool {tool_name}: {e}")
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "error": {
                                    "code": -32603,
                                    "message": f"Tool execution error: {str(e)}"
                                }
                            }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"Tool not found: {tool_name}"
                            }
                        }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                    
            except Exception as e:
                logger.error(f"Error processing MCP request: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_data.get("id", None) if 'request_data' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
        
        return app
        
    except ImportError as e:
        logger.error(f"FastAPI not available for HTTP transport: {e}")
        return None


def main():
    """Entry point for console script."""
    try:
        # Check transport mode via environment variable
        transport_mode = os.getenv("MCP_TRANSPORT", "stdio").lower()
        
        if transport_mode == "http":
            # HTTP transport for Fargate deployment
            logger.info("Starting DataZone MCP server with HTTP transport")
            
            # Create FastAPI app with real MCP tools
            app = create_http_app()
            if not app:
                sys.exit(1)
            
            # Get configuration from environment
            host = os.getenv("HOST", "0.0.0.0")
            port = int(os.getenv("PORT", "8080"))
            
            # Start server with uvicorn
            import uvicorn
            uvicorn.run(app, host=host, port=port, log_level="info")
        else:
            # Default stdio transport for local development
            logger.info("Starting DataZone MCP server with stdio transport")
            
            # Create and run MCP server with stdio
            mcp = create_mcp_server()
            mcp.run()

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
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
