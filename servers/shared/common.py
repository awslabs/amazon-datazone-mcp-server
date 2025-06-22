"""
Common utilities shared across all MCP servers.
"""

import json
import sys
import traceback
import logging
from typing import Dict, Any


def setup_logging(server_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up consistent logging configuration for all MCP servers.
    
    Args:
        server_name (str): Name of the server for logging context
        level (int): Logging level (default: INFO)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logging.basicConfig(
        level=level,
        format=f'%(asctime)s - {server_name} - %(levelname)s - %(message)s',
        stream=sys.stderr
    )
    return logging.getLogger(server_name)


def create_error_response(
    error: Exception,
    server_name: str,
    operation: str = None,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response for MCP servers.
    
    Args:
        error (Exception): The exception that occurred
        server_name (str): Name of the server where error occurred
        operation (str, optional): The operation that failed
        context (Dict[str, Any], optional): Additional context
    
    Returns:
        Dict[str, Any]: Formatted error response
    """
    error_response = {
        "error": str(error),
        "type": type(error).__name__,
        "message": f"MCP server {server_name} encountered an error",
        "details": {
            "server": server_name,
            "status": "failed",
            "traceback": traceback.format_exc()
        }
    }
    
    if operation:
        error_response["details"]["operation"] = operation
    
    if context:
        error_response["details"]["context"] = context
    
    return error_response


def log_error_and_exit(
    error: Exception,
    logger: logging.Logger,
    server_name: str,
    operation: str = None,
    context: Dict[str, Any] = None,
    exit_code: int = 1
):
    """
    Log an error and exit the process with proper error response.
    
    Args:
        error (Exception): The exception that occurred
        logger (logging.Logger): Logger instance
        server_name (str): Name of the server
        operation (str, optional): The operation that failed
        context (Dict[str, Any], optional): Additional context
        exit_code (int): Exit code (default: 1)
    """
    logger.error(f"Failed to start {server_name} MCP server: {str(error)}")
    logger.error(traceback.format_exc())
    
    error_response = create_error_response(error, server_name, operation, context)
    print(json.dumps(error_response), file=sys.stderr)
    sys.exit(exit_code)


def validate_aws_credentials() -> bool:
    """
    Validate that AWS credentials are available.
    
    Returns:
        bool: True if credentials are available, False otherwise
    """
    try:
        import boto3
        # Try to get the caller identity to verify credentials
        sts_client = boto3.client('sts')
        sts_client.get_caller_identity()
        return True
    except Exception:
        return False 