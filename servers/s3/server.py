# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""S3 MCP Server implementation."""

import json
import logging
import os
import sys
import traceback
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def get_mcp_credentials():
    """Retrieve MCP AWS credentials from environment variables or Secrets Manager"""
    try:
        # Only use environment variables for local development (specific session key pattern)
        # In AWS/ECS, always use Secrets Manager even if task role credentials exist
        local_access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
        if (
            local_access_key.startswith(
                "ASIAQGYBP5OXW5MTKVKQ"
            )  # pragma: allowlist secret
            and os.environ.get("AWS_SECRET_ACCESS_KEY")
            and os.environ.get("AWS_SESSION_TOKEN")
        ):
            logger.info(
                " Using MCP credentials from environment variables (local development)"
            )
            return {
                "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID"),
                "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
                "aws_session_token": os.environ.get("AWS_SESSION_TOKEN"),
                "region_name": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
                "account_id": "014498655151",
            }

        # For AWS deployment, always retrieve from Secrets Manager
        logger.info(
            " Running in AWS environment - retrieving MCP credentials from Secrets Manager..."
        )
        secrets_client = boto3.client("secretsmanager", region_name="us-east-1")

        # Get the secret
        secret_name = "smus-ai/dev/mcp-aws-credentials"  # pragma: allowlist secret
        logger.info(f"Retrieving MCP credentials from secret: {secret_name}")

        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_value = json.loads(response["SecretString"])

        logger.info(
            f" Successfully retrieved MCP credentials from Secrets Manager for account: {secret_value.get('ACCOUNT_ID', 'unknown')}"
        )
        return {
            "aws_access_key_id": secret_value["AWS_ACCESS_KEY_ID"],
            "aws_secret_access_key": secret_value["AWS_SECRET_ACCESS_KEY"],
            "aws_session_token": secret_value["AWS_SESSION_TOKEN"],
            "region_name": secret_value["AWS_DEFAULT_REGION"],
            "account_id": secret_value.get("ACCOUNT_ID", "unknown"),
        }

    except Exception as e:
        logger.error(f" Failed to retrieve MCP credentials from Secrets Manager: {e}")
        # Fall back to default credentials
        logger.warning(" Falling back to default AWS credentials")
        return None


# Initialize MCP credentials and create boto3 session
mcp_credentials = get_mcp_credentials()

# Initialize FastMCP server
mcp = FastMCP("s3")

# Initialize boto3 client with explicit credentials
try:
    if mcp_credentials:
        # Create session with explicit credentials
        session = boto3.Session(
            aws_access_key_id=mcp_credentials["aws_access_key_id"],
            aws_secret_access_key=mcp_credentials["aws_secret_access_key"],
            aws_session_token=mcp_credentials["aws_session_token"],
            region_name=mcp_credentials["region_name"],
        )
        s3_client = session.client("s3")
        logger.info(
            f"Successfully initialized S3 client with MCP credentials for account: {mcp_credentials.get('account_id', 'unknown')}"
        )

        # Verify credentials with STS get_caller_identity
        try:
            sts_client = session.client("sts")
            identity = sts_client.get_caller_identity()
            actual_account = identity.get("Account", "unknown")
            user_arn = identity.get("Arn", "unknown")
            logger.info(
                f" STS VERIFICATION SUCCESS - S3 MCP connected to AWS Account: {actual_account}"
            )
            logger.info(f" STS Identity ARN: {user_arn}")

            # Log warning if account mismatch
            expected_account = mcp_credentials.get("account_id", "014498655151")
            if actual_account != expected_account:
                logger.warning(
                    f" ACCOUNT MISMATCH - Expected: {expected_account}, Actual: {actual_account}"
                )
            else:
                logger.info(
                    f" ACCOUNT MATCH CONFIRMED - Using correct account: {actual_account}"
                )

        except Exception as sts_error:
            logger.error(
                f" STS VERIFICATION FAILED - Cannot verify AWS credentials: {sts_error}"
            )

    else:
        # Fall back to default credentials
        s3_client = boto3.client("s3")
        logger.info("Initialized S3 client with default credentials")

        # Verify default credentials with STS
        try:
            sts_client = boto3.client("sts")
            identity = sts_client.get_caller_identity()
            actual_account = identity.get("Account", "unknown")
            user_arn = identity.get("Arn", "unknown")
            logger.info(
                f" STS VERIFICATION (DEFAULT) - S3 MCP connected to AWS Account: {actual_account}"
            )
            logger.info(f" STS Identity ARN: {user_arn}")
        except Exception as sts_error:
            logger.error(
                f" STS VERIFICATION FAILED (DEFAULT) - Cannot verify AWS credentials: {sts_error}"
            )

except Exception as e:
    logger.error(f"Failed to initialize S3 client: {str(e)}")
    # Don't raise - allow server to start without credentials for testing
    s3_client = None


@mcp.tool()
async def s3_read_file(
    bucket_name: str,
    file_path: str,
) -> Any:
    """
    Reads a file from S3 and returns its contents.

    Args:
        bucket_name (str): The name of the S3 bucket
        file_path (str): The path to the file in the bucket

    Returns:
        Any: The file contents and metadata
    """
    try:
        logger.info(f"Reading file {file_path} from bucket {bucket_name}")

        # Get the object
        response = s3_client.get_object(Bucket=bucket_name, Key=file_path)

        # Read the content
        content = response["Body"].read()

        # For text files, decode to string
        content_type = response.get("ContentType", "")
        if content_type.startswith("text/") or file_path.endswith(
            (".txt", ".csv", ".json", ".md")
        ):
            try:
                content = content.decode("utf-8")
            except UnicodeDecodeError:
                # If it's not UTF-8 decodable, keep as binary
                pass

        # Return content and metadata
        return {
            "content": content,
            "metadata": {
                "content_type": response.get("ContentType"),
                "content_length": response.get("ContentLength"),
                "last_modified": (
                    response.get("LastModified").isoformat()
                    if response.get("LastModified")
                    else None
                ),
                "etag": response.get("ETag"),
            },
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            logger.error(f"File {file_path} not found in bucket {bucket_name}")
            raise Exception(f"File {file_path} not found in bucket {bucket_name}")
        elif error_code == "AccessDenied":
            logger.error(f"Access denied to file {file_path} in bucket {bucket_name}")
            raise Exception(
                f"Access denied to file {file_path} in bucket {bucket_name}"
            )
        else:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise Exception(f"Error reading file {file_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error reading file {file_path}: {str(e)}")
        raise Exception(f"Unexpected error reading file {file_path}: {str(e)}")


@mcp.tool()
async def s3_list_objects(
    bucket_name: str, prefix: str = "", max_items: int = 100
) -> Dict[str, Any]:
    """
    Lists objects in an S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket
        prefix (str, optional): Prefix to filter objects (like a folder path)
        max_items (int, optional): Maximum number of items to return

    Returns:
        Dict containing:
            - bucket: The bucket name
            - prefix: The prefix used for filtering
            - objects: List of objects with:
                - key: Object key
                - size_bytes: Size in bytes
                - last_modified: Last modified timestamp
                - type: Inferred file type
            - common_prefixes: List of folder prefixes
    """
    try:
        logger.info(f"Listing objects in bucket {bucket_name} with prefix {prefix}")

        # List objects in the bucket
        if prefix and not prefix.endswith("/"):
            prefix = prefix + "/"

        response = s3_client.list_objects_v2(
            Bucket=bucket_name, Prefix=prefix, MaxKeys=max_items, Delimiter="/"
        )

        result = {
            "bucket": bucket_name,
            "prefix": prefix,
            "objects": [],
            "common_prefixes": [],
        }

        # Handle objects (files)
        for obj in response.get("Contents", []):
            # Skip the prefix itself if it was included
            if obj.get("Key") == prefix:
                continue

            # Infer file type from extension
            key = obj.get("Key", "")
            file_type = "unknown"
            if key.endswith(".csv"):
                file_type = "csv"
            elif key.endswith(".json"):
                file_type = "json"
            elif key.endswith(".parquet"):
                file_type = "parquet"
            elif any(key.endswith(ext) for ext in [".txt", ".log", ".md"]):
                file_type = "text"
            elif any(key.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif"]):
                file_type = "image"
            elif key.endswith("/"):
                file_type = "folder"

            result["objects"].append(
                {
                    "key": key,
                    "size_bytes": obj.get("Size"),
                    "last_modified": (
                        obj.get("LastModified").isoformat()
                        if obj.get("LastModified")
                        else None
                    ),
                    "type": file_type,
                }
            )

        # Handle common prefixes (folders)
        for prefix_obj in response.get("CommonPrefixes", []):
            prefix_path = prefix_obj.get("Prefix")
            result["common_prefixes"].append({"prefix": prefix_path, "type": "folder"})

        logger.info(f"Successfully listed objects in bucket {bucket_name}")
        return result

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            logger.error(f"Bucket {bucket_name} does not exist")
            raise Exception(f"Bucket {bucket_name} does not exist")
        elif error_code == "AccessDenied":
            logger.error(f"Access denied to bucket {bucket_name}")
            raise Exception(f"Access denied to bucket {bucket_name}")
        else:
            logger.error(f"Error listing objects in bucket {bucket_name}: {str(e)}")
            raise Exception(f"Error listing objects in bucket {bucket_name}: {str(e)}")
    except Exception as e:
        logger.error(
            f"Unexpected error listing objects in bucket {bucket_name}: {str(e)}"
        )
        raise Exception(
            f"Unexpected error listing objects in bucket {bucket_name}: {str(e)}"
        )


@mcp.tool()
async def s3_head_object(
    bucket_name: str, object_key: str, version_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves metadata from an S3 object without returning the object itself.

    Args:
        bucket_name (str): The name of the S3 bucket
        object_key (str): The key of the object
        version_id (str, optional): The version ID of the object (default: None)

    Returns:
        Dict containing:
            - LastModified: Last modified timestamp
            - ContentLength: Size of the object in bytes
            - ContentType: Content type of the object
            - ETag: Entity tag of the object
            - VersionId: Version ID if versioning is enabled
            - StorageClass: Storage class of the object
            - Metadata: User-defined metadata
    """
    try:
        logger.info(
            f"Retrieving metadata for object {object_key} in bucket {bucket_name}"
        )

        # Prepare request parameters
        params = {"Bucket": bucket_name, "Key": object_key}

        if version_id:
            params["VersionId"] = version_id

        # Make the API call
        response = s3_client.head_object(**params)

        # Extract relevant metadata
        metadata = {
            "LastModified": response.get("LastModified"),
            "ContentLength": response.get("ContentLength"),
            "ContentType": response.get("ContentType"),
            "ETag": response.get("ETag"),
            "VersionId": response.get("VersionId"),
            "StorageClass": response.get("StorageClass"),
            "Metadata": response.get("Metadata", {}),
            "RestoreStatus": response.get("Restore"),
            "ArchiveStatus": response.get("ArchiveStatus"),
        }

        logger.info(f"Successfully retrieved metadata for object {object_key}")
        return metadata

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            logger.error(f"Object {object_key} not found in bucket {bucket_name}")
            raise Exception(f"Object {object_key} not found in bucket {bucket_name}")
        elif error_code == "403":
            logger.error(
                f"Access denied to object {object_key} in bucket {bucket_name}"
            )
            raise Exception(
                f"Access denied to object {object_key} in bucket {bucket_name}"
            )
        else:
            logger.error(f"Error retrieving metadata for object {object_key}: {str(e)}")
            raise Exception(
                f"Error retrieving metadata for object {object_key}: {str(e)}"
            )
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving metadata for object {object_key}: {str(e)}"
        )
        raise Exception(
            f"Unexpected error retrieving metadata for object {object_key}: {str(e)}"
        )


@mcp.tool()
async def s3_list_buckets() -> Dict[str, Any]:
    """
    Lists all S3 buckets accessible to the user.

    Returns:
        Dict containing:
            - buckets: List of bucket information including:
                - name: Bucket name
                - creation_date: Bucket creation date
    """
    try:
        logger.info("Listing all accessible S3 buckets")

        # List buckets
        response = s3_client.list_buckets()

        # Format the response
        buckets = []
        for bucket in response.get("Buckets", []):
            buckets.append(
                {
                    "name": bucket.get("Name"),
                    "creation_date": (
                        bucket.get("CreationDate").isoformat()
                        if bucket.get("CreationDate")
                        else None
                    ),
                }
            )

        result = {"buckets": buckets}

        logger.info(f"Successfully listed {len(buckets)} buckets")
        return result

    except Exception as e:
        logger.error(f"Error listing S3 buckets: {str(e)}")
        raise Exception(f"Error listing S3 buckets: {str(e)}")


@mcp.tool()
async def s3_upload_object(
    bucket_name: str, object_key: str, content: str, content_type: str = "text/plain"
) -> Dict[str, Any]:
    """
    Uploads content to an S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket
        object_key (str): The key to assign to the object
        content (str): The content to upload
        content_type (str, optional): The content type (default: "text/plain")

    Returns:
        Dict containing:
            - etag: The ETag of the uploaded object
            - status: Upload status
            - bucket: Bucket name
            - key: Object key
    """
    try:
        logger.info(f"Uploading object {object_key} to bucket {bucket_name}")

        # Upload the content
        response = s3_client.put_object(
            Bucket=bucket_name, Key=object_key, Body=content, ContentType=content_type
        )

        result = {
            "etag": response.get("ETag"),
            "status": "success",
            "bucket": bucket_name,
            "key": object_key,
        }

        logger.info(f"Successfully uploaded object {object_key}")
        return result

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDenied":
            logger.error(f"Access denied to bucket {bucket_name}")
            raise Exception(f"Access denied to bucket {bucket_name}")
        else:
            logger.error(f"Error uploading to bucket {bucket_name}: {str(e)}")
            raise Exception(f"Error uploading to bucket {bucket_name}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error uploading to bucket {bucket_name}: {str(e)}")
        raise Exception(f"Unexpected error uploading to bucket {bucket_name}: {str(e)}")


@mcp.tool()
async def s3_get_object(
    bucket_name: str,
    object_key: str,
    version_id: Optional[str] = None,
    range_start: Optional[int] = None,
    range_end: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Retrieves an object from Amazon S3.

    Args:
        bucket_name (str): The name of the S3 bucket
        object_key (str): The key of the object
        version_id (str, optional): Version ID of the object (default: None)
        range_start (int, optional): Start byte for range request (default: None)
        range_end (int, optional): End byte for range request (default: None)

    Returns:
        Dict containing:
            - Body: The object data
            - ContentType: Content type of the object
            - ContentLength: Size of the object in bytes
            - LastModified: Last modified timestamp
            - ETag: Entity tag of the object
            - VersionId: Version ID if versioning is enabled
            - Metadata: User-defined metadata
            - StorageClass: Storage class of the object
    """
    try:
        logger.info(f"Retrieving object {object_key} from bucket {bucket_name}")

        # Prepare request parameters
        params = {"Bucket": bucket_name, "Key": object_key}

        # Add optional parameters
        if version_id:
            params["VersionId"] = version_id

        if range_start is not None and range_end is not None:
            params["Range"] = f"bytes={range_start}-{range_end}"

        # Make the API call
        response = s3_client.get_object(**params)

        # Extract relevant information
        result = {
            "Body": response["Body"].read(),
            "ContentType": response.get("ContentType"),
            "ContentLength": response.get("ContentLength"),
            "LastModified": response.get("LastModified"),
            "ETag": response.get("ETag"),
            "VersionId": response.get("VersionId"),
            "Metadata": response.get("Metadata", {}),
            "StorageClass": response.get("StorageClass"),
        }

        logger.info(f"Successfully retrieved object {object_key}")
        return result

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            logger.error(f"Object {object_key} not found in bucket {bucket_name}")
            raise Exception(f"Object {object_key} not found in bucket {bucket_name}")
        elif error_code == "403":
            logger.error(
                f"Access denied to object {object_key} in bucket {bucket_name}"
            )
            raise Exception(
                f"Access denied to object {object_key} in bucket {bucket_name}"
            )
        else:
            logger.error(f"Error retrieving object {object_key}: {str(e)}")
            raise Exception(f"Error retrieving object {object_key}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error retrieving object {object_key}: {str(e)}")
        raise Exception(f"Unexpected error retrieving object {object_key}: {str(e)}")


def create_http_app():
    """Create FastAPI app for HTTP transport"""
    try:
        from fastapi import FastAPI, Request

        app = FastAPI(
            title="S3 MCP Server",
            description="MCP server for AWS S3 service",
            version="1.0.0",
        )

        @app.get("/health")
        async def health_check():
            """Health check endpoint for ALB"""
            # Get the actual tool count from FastMCP's tool manager
            tool_count = len(mcp._tool_manager._tools)
            return {
                "status": "healthy",
                "service": "s3-mcp-server",
                "version": "1.0.0",
                "transport": "http",
                "tools_count": tool_count,
            }

        @app.get("/")
        def root():
            """Root endpoint with service info"""
            # Get actual tools from FastMCP's tool manager
            tools_available = list(mcp._tool_manager._tools.keys())
            return {
                "service": "S3 MCP Server",
                "status": "running",
                "transport": "http",
                "endpoints": ["/health", "/mcp/s3"],
                "tools_available": tools_available,
            }

        @app.get("/mcp/s3")
        def mcp_root():
            """MCP root endpoint"""
            return {
                "jsonrpc": "2.0",
                "method": "initialize",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "s3-mcp-server", "version": "1.0.0"},
                },
            }

        @app.post("/mcp/s3")
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
                            input_schema = (
                                tool_obj.model_json_schema()
                                if hasattr(tool_obj, "model_json_schema")
                                else {
                                    "type": "object",
                                    "properties": {},
                                    "required": [],
                                }
                            )

                            tool_info = {
                                "name": tool_name,
                                "description": tool_obj.description
                                or f"S3 tool: {tool_name}",
                                "inputSchema": input_schema,
                            }
                        except Exception:
                            # Fallback if schema generation fails
                            tool_info = {
                                "name": tool_name,
                                "description": tool_obj.description
                                or f"S3 tool: {tool_name}",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": [],
                                },
                            }
                        tools.append(tool_info)

                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"tools": tools},
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
                                    "content": [{"type": "text", "text": result_text}]
                                },
                            }
                        except Exception as e:
                            logger.error(f"Error calling tool {tool_name}: {e}")
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "error": {
                                    "code": -32603,
                                    "message": f"Tool execution error: {str(e)}",
                                },
                            }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"Tool not found: {tool_name}",
                            },
                        }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}",
                        },
                    }

            except Exception as e:
                logger.error(f"Error processing MCP request: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_data.get("id", None)
                    if "request_data" in locals()
                    else None,
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                }

        return app

    except ImportError as e:
        logger.error(f"FastAPI not available for HTTP transport: {e}")
        return None


# Start the MCP server
if __name__ == "__main__":
    try:
        logger.info("Starting S3 MCP server")
        # Debug info for troubleshooting
        logger.info(f"FastMCP version: {getattr(FastMCP, '__version__', 'unknown')}")
        logger.info(f"Number of registered tools: {len(getattr(mcp, '_tools', []))}")

        # Check transport mode via environment variable
        transport_mode = os.getenv("MCP_TRANSPORT", "stdio").lower()

        if transport_mode == "http":
            # HTTP transport for Docker deployment
            logger.info("Starting S3 MCP server with HTTP transport")

            app = create_http_app()
            if not app:
                sys.exit(1)

            # Get configuration from environment
            host = os.getenv("HOST", "0.0.0.0")
            port = int(os.getenv("PORT", "8083"))

            # Start server with uvicorn
            import uvicorn

            uvicorn.run(app, host=host, port=port, log_level="info")
        else:
            # Default stdio transport
            logger.info("Starting S3 MCP server with stdio transport")
            mcp.run(transport="stdio")

    except Exception as e:
        logger.error(f"Failed to start S3 MCP server: {str(e)}")
        logger.error(traceback.format_exc())
        # Create a proper JSON error response
        error_response = {
            "error": str(e),
            "type": type(e).__name__,
            "message": "MCP server encountered an error",
            "details": {
                "server": "s3",
                "status": "failed",
                "traceback": traceback.format_exc(),
            },
        }
        print(json.dumps(error_response), file=sys.stderr)
        sys.exit(1)
