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

import json
import logging
import os
import sys
import traceback
from typing import Any, Dict, List, Optional

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
        local_access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")  # pragma: allowlist secret
        if (
            local_access_key.startswith(
                "ASIAQGYBP5OXW5MTKVKQ"
            )  # pragma: allowlist secret
            and os.environ.get("AWS_SECRET_ACCESS_KEY")  # pragma: allowlist secret
            and os.environ.get("AWS_SESSION_TOKEN")  # pragma: allowlist secret
        ):
            logger.info(
                " Using MCP credentials from environment variables (local development)"
            )
            return {
                "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID"),  # pragma: allowlist secret
                "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),  # pragma: allowlist secret
                "aws_session_token": os.environ.get("AWS_SESSION_TOKEN"),  # pragma: allowlist secret
                "region_name": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),  # pragma: allowlist secret
                "account_id": "014498655151",  # pragma: allowlist secret
            }

        # For AWS deployment, always retrieve from Secrets Manager
        logger.info(
            " Running in AWS environment - retrieving MCP credentials from Secrets Manager..."
        )
        secrets_client = boto3.client("secretsmanager", region_name="us-east-1")  # pragma: allowlist secret

        # Get the secret
        secret_name = "smus-ai/dev/mcp-aws-credentials"  # pragma: allowlist secret
        logger.info(f"Retrieving MCP credentials from secret: {secret_name}")

        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_value = json.loads(response["SecretString"])

        logger.info(
            f" Successfully retrieved MCP credentials from Secrets Manager for account: {secret_value.get('ACCOUNT_ID', 'unknown')}"
        )
        return {
            "aws_access_key_id": secret_value["AWS_ACCESS_KEY_ID"],  # pragma: allowlist secret
            "aws_secret_access_key": secret_value["AWS_SECRET_ACCESS_KEY"],  # pragma: allowlist secret
            "aws_session_token": secret_value["AWS_SESSION_TOKEN"],  # pragma: allowlist secret
            "region_name": secret_value["AWS_DEFAULT_REGION"],  # pragma: allowlist secret
            "account_id": secret_value.get("ACCOUNT_ID", "unknown"),  # pragma: allowlist secret
        }

    except Exception as e:
        logger.error(f" Failed to retrieve MCP credentials from Secrets Manager: {e}")
        # Fall back to default credentials
        logger.warning(" Falling back to default AWS credentials")
        return None


# Initialize MCP credentials and create boto3 session
mcp_credentials = get_mcp_credentials()

# Initialize FastMCP server
mcp = FastMCP("glue")

# Constants
USER_AGENT = "glue-app/1.0"

# Initialize boto3 client with explicit credentials
try:
    if mcp_credentials:
        # Create session with explicit credentials
        session = boto3.Session(
            aws_access_key_id=mcp_credentials["aws_access_key_id"],  # pragma: allowlist secret
            aws_secret_access_key=mcp_credentials["aws_secret_access_key"],  # pragma: allowlist secret
            aws_session_token=mcp_credentials["aws_session_token"],  # pragma: allowlist secret
            region_name=mcp_credentials["region_name"],  # pragma: allowlist secret
        )
        glue_client = session.client("glue")
        logger.info(
            f"Successfully initialized Glue client with MCP credentials for account: {mcp_credentials.get('account_id', 'unknown')}"
        )

        # Verify credentials with STS get_caller_identity
        try:
            sts_client = session.client("sts")
            identity = sts_client.get_caller_identity()
            actual_account = identity.get("Account", "unknown")
            user_arn = identity.get("Arn", "unknown")
            logger.info(
                f" STS VERIFICATION SUCCESS - Glue MCP connected to AWS Account: {actual_account}"
            )
            logger.info(f" STS Identity ARN: {user_arn}")

            # Log warning if account mismatch
            expected_account = mcp_credentials.get("account_id", "014498655151")  # pragma: allowlist secret
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
        glue_client = boto3.client("glue")
        logger.info("Initialized Glue client with default credentials")

        # Verify default credentials with STS
        try:
            sts_client = boto3.client("sts")
            identity = sts_client.get_caller_identity()
            actual_account = identity.get("Account", "unknown")
            user_arn = identity.get("Arn", "unknown")
            logger.info(
                f" STS VERIFICATION (DEFAULT) - Glue MCP connected to AWS Account: {actual_account}"
            )
            logger.info(f" STS Identity ARN: {user_arn}")
        except Exception as sts_error:
            logger.error(
                f" STS VERIFICATION FAILED (DEFAULT) - Cannot verify AWS credentials: {sts_error}"
            )

except Exception as e:
    logger.error(f"Failed to initialize Glue client: {str(e)}")
    # Don't raise - allow server to start without credentials for testing
    glue_client = None


@mcp.tool()
async def glue_create_database(
    name: str,
    catalog_id: Optional[str] = None,
    description: Optional[str] = None,
    location_uri: Optional[str] = None,
    parameters: Optional[Dict[str, str]] = None,
    tags: Optional[Dict[str, str]] = None,
    create_table_default_permissions: Optional[List[Dict[str, Any]]] = None,
    federated_database: Optional[Dict[str, str]] = None,
    target_database: Optional[Dict[str, str]] = None,
) -> Any:
    """
    Creates a new database in the AWS Glue Data Catalog.

    Args:
        name (str): The name of the database to create
        catalog_id (str, optional): The ID of the Data Catalog in which to create the database
        description (str, optional): Description of the database
        location_uri (str, optional): The location of the database (for example, an HDFS path)
        parameters (Dict[str, str], optional): These key-value pairs define parameters and properties of the database
        tags (Dict[str, str], optional): The tags you assign to the database
        create_table_default_permissions (List[Dict[str, Any]], optional): Creates a set of default permissions on the table
        federated_database (Dict[str, str], optional): A FederatedDatabase structure that references an external database
        target_database (Dict[str, str], optional): A structure that describes a target database for resource linking

    Returns:
        Any: The API response containing the created database details
    """
    try:
        logger.info(f"Creating database: {name}")
        # Prepare the request parameters
        database_input: Dict[str, Any] = {"Name": name}

        # Add optional parameters if provided
        if description is not None:
            database_input["Description"] = description
        if location_uri is not None:
            database_input["LocationUri"] = location_uri
        if parameters is not None:
            database_input["Parameters"] = parameters
        if create_table_default_permissions is not None:
            database_input["CreateTableDefaultPermissions"] = (
                create_table_default_permissions
            )
        if federated_database is not None:
            database_input["FederatedDatabase"] = federated_database
        if target_database is not None:
            database_input["TargetDatabase"] = target_database

        # Prepare the request
        params: Dict[str, Any] = {"DatabaseInput": database_input}

        # Add optional catalog_id if provided
        if catalog_id:
            params["CatalogId"] = catalog_id

        # Add optional tags if provided
        if tags:
            params["Tags"] = tags

        if not glue_client:
            raise Exception("Glue client not initialized")
        response = glue_client.create_database(**params)
        logger.info(f"Successfully created database: {name}")
        return response
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        error_details = {
            "error": error_code,
            "message": error_message,
            "operation": "create_database",
            "database": name,
        }
        logger.error(json.dumps(error_details))

        if error_code == "AlreadyExistsException":
            raise Exception(f"Database {name} already exists")
        elif error_code == "InvalidInputException":
            raise Exception(f"Invalid input provided for creating database {name}")
        elif error_code == "OperationTimeoutException":
            raise Exception(f"Operation timed out while creating database {name}")
        elif error_code == "ResourceNumberLimitExceededException":
            raise Exception(f"Resource limit exceeded while creating database {name}")
        else:
            raise Exception(f"Error creating database {name}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in create_database: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"Unexpected error creating database {name}: {str(e)}")


@mcp.tool()
async def glue_create_crawler(
    name: str,
    role: str,
    targets: Dict[str, List[Dict[str, Any]]],
    database_name: Optional[str] = None,
    classifiers: Optional[List[str]] = None,
    configuration: Optional[str] = None,
    crawler_security_configuration: Optional[str] = None,
    description: Optional[str] = None,
    lake_formation_configuration: Optional[Dict[str, Any]] = None,
    lineage_configuration: Optional[Dict[str, str]] = None,
    recrawl_policy: Optional[Dict[str, str]] = None,
    schedule: Optional[str] = None,
    schema_change_policy: Optional[Dict[str, str]] = None,
    table_prefix: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
) -> Any:
    """
    Creates a new crawler with specified targets, role, configuration, and optional schedule.

    Args:
        name (str): Name of the new crawler
        role (str): The IAM role or ARN of an IAM role used by the new crawler to access customer resources
        targets (Dict[str, List[Dict[str, Any]]]): A list of collection of targets to crawl
        database_name (str, optional): The AWS Glue database where results are written
        classifiers (List[str], optional): List of custom classifiers that override default classifiers
        configuration (str, optional): Crawler configuration information as a versioned JSON string
        crawler_security_configuration (str, optional): Name of the SecurityConfiguration structure to use
        description (str, optional): Description of the new crawler
        lake_formation_configuration (Dict[str, Any], optional): AWS Lake Formation configuration settings
        lineage_configuration (Dict[str, str], optional): Data lineage configuration settings
        recrawl_policy (Dict[str, str], optional): Policy for recrawling
        schedule (str, optional): A cron expression used to specify the schedule
        schema_change_policy (Dict[str, str], optional): Policy for the crawler's update and deletion behavior
        table_prefix (str, optional): The table prefix used for catalog tables that are created
        tags (Dict[str, str], optional): Tags to use with this crawler request

    Returns:
        Any: The API response containing the created crawler details
    """
    try:
        logger.info(f"Creating crawler: {name}")
        # Prepare the request parameters
        params: Dict[str, Any] = {"Name": name, "Role": role, "Targets": targets}

        # Add optional parameters if provided
        if database_name:
            params["DatabaseName"] = database_name
        if classifiers:
            params["Classifiers"] = classifiers
        if configuration:
            params["Configuration"] = configuration
        if crawler_security_configuration:
            params["CrawlerSecurityConfiguration"] = crawler_security_configuration
        if description:
            params["Description"] = description
        if lake_formation_configuration:
            params["LakeFormationConfiguration"] = lake_formation_configuration
        if lineage_configuration:
            params["LineageConfiguration"] = lineage_configuration
        if recrawl_policy:
            params["RecrawlPolicy"] = recrawl_policy
        if schedule:
            params["Schedule"] = schedule
        if schema_change_policy:
            params["SchemaChangePolicy"] = schema_change_policy
        if table_prefix:
            params["TablePrefix"] = table_prefix
        if tags:
            params["Tags"] = tags

        if not glue_client:
            raise Exception("Glue client not initialized")
        response = glue_client.create_crawler(**params)
        logger.info(f"Successfully created crawler: {name}")
        return response
    except ClientError as e:
        logger.error(f"ClientError in create_crawler: {str(e)}")
        raise Exception(f"Error creating crawler {name}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in create_crawler: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"Unexpected error creating crawler {name}: {str(e)}")


@mcp.tool()
async def glue_start_crawler(name: str) -> Any:
    """
    Starts a crawl using the specified crawler, regardless of what is scheduled.

    Args:
        name (str): Name of the crawler to start

    Returns:
        Any: The API response (empty on success)
    """
    try:
        logger.info(f"Starting crawler: {name}")
        if not glue_client:
            raise Exception("Glue client not initialized")
        response = glue_client.start_crawler(Name=name)
        logger.info(f"Successfully started crawler: {name}")
        return response
    except ClientError as e:
        logger.error(f"ClientError in start_crawler: {str(e)}")
        raise Exception(f"Error starting crawler {name}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in start_crawler: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"Unexpected error starting crawler {name}: {str(e)}")


@mcp.tool()
async def glue_get_crawler(name: str) -> Any:
    """
    Retrieves metadata for a specified crawler.

    Args:
        name (str): The name of the crawler to retrieve metadata for

    Returns:
        Any: The API response containing crawler metadata
    """
    try:
        logger.info(f"Getting crawler: {name}")
        if not glue_client:
            raise Exception("Glue client not initialized")
        response = glue_client.get_crawler(Name=name)
        logger.info(f"Successfully retrieved crawler: {name}")
        return response
    except ClientError as e:
        logger.error(f"ClientError in get_crawler: {str(e)}")
        raise Exception(f"Error getting crawler {name}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in get_crawler: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"Unexpected error getting crawler {name}: {str(e)}")


@mcp.tool()
async def glue_get_tables(
    database_name: str,
    catalog_id: Optional[str] = None,
    expression: Optional[str] = None,
    include_status_details: bool = False,
    max_results: int = 100,
    next_token: Optional[str] = None,
    query_as_of_time: Optional[int] = None,
    transaction_id: Optional[str] = None,
    attributes_to_get: Optional[List[str]] = None,
) -> Any:
    """
    Retrieves the definitions of some or all of the tables in a given database.

    Args:
        database_name (str): The database in the catalog whose tables to list
        catalog_id (str, optional): The ID of the Data Catalog where the tables reside
        expression (str, optional): A regular expression pattern to filter table names
        include_status_details (bool, optional): Whether to include status details for views
        max_results (int, optional): Maximum number of tables to return (1-100, default: 100)
        next_token (str, optional): Token for pagination
        query_as_of_time (int, optional): The time as of when to read the table contents
        transaction_id (str, optional): The transaction ID at which to read the table contents
        attributes_to_get (List[str], optional): Specifies the table fields to return

    Returns:
        Any: The API response containing table definitions
    """
    try:
        logger.info(f"Getting tables from database: {database_name}")
        # Prepare the request parameters
        params = {
            "DatabaseName": database_name,
            "MaxResults": min(
                max_results, 100
            ),  # Ensure maxResults is within valid range
        }

        # Add optional parameters if provided
        if catalog_id:
            params["CatalogId"] = catalog_id
        if expression:
            params["Expression"] = expression
        if include_status_details:
            params["IncludeStatusDetails"] = include_status_details
        if next_token:
            params["NextToken"] = next_token
        if query_as_of_time:
            params["QueryAsOfTime"] = query_as_of_time
        if transaction_id:
            params["TransactionId"] = transaction_id
        if attributes_to_get:
            params["AttributesToGet"] = attributes_to_get

        if not glue_client:
            raise Exception("Glue client not initialized")
        response = glue_client.get_tables(**params)
        logger.info(f"Successfully retrieved tables from database: {database_name}")
        return response
    except ClientError as e:
        logger.error(f"ClientError in get_tables: {str(e)}")
        raise Exception(f"Error getting tables from database {database_name}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in get_tables: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(
            f"Unexpected error getting tables from database {database_name}: {str(e)}"
        )


@mcp.tool()
async def glue_get_table(
    database_name: str,
    name: str,
    catalog_id: Optional[str] = None,
    include_status_details: bool = False,
    query_as_of_time: Optional[int] = None,
    transaction_id: Optional[str] = None,
) -> Any:
    """
    Retrieves the Table definition in a Data Catalog for a specified table.

    Args:
        database_name (str): The name of the database in the catalog in which the table resides
        name (str): The name of the table for which to retrieve the definition
        catalog_id (str, optional): The ID of the Data Catalog where the table resides
        include_status_details (bool, optional): Whether to include status details for views
        query_as_of_time (int, optional): The time as of when to read the table contents
        transaction_id (str, optional): The transaction ID at which to read the table contents

    Returns:
        Any: The API response containing the Table object
    """
    try:
        logger.info(f"Getting table {name} from database: {database_name}")
        # Prepare the request parameters
        params: Dict[str, Any] = {"DatabaseName": database_name, "Name": name}

        # Add optional parameters if provided
        if catalog_id:
            params["CatalogId"] = catalog_id
        if include_status_details:
            params["IncludeStatusDetails"] = include_status_details
        if query_as_of_time:
            params["QueryAsOfTime"] = query_as_of_time
        if transaction_id:
            params["TransactionId"] = transaction_id

        if not glue_client:
            raise Exception("Glue client not initialized")
        response = glue_client.get_table(**params)
        logger.info(
            f"Successfully retrieved table {name} from database: {database_name}"
        )
        return response
    except ClientError as e:
        logger.error(f"ClientError in get_table: {str(e)}")
        raise Exception(
            f"Error getting table {name} from database {database_name}: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_table: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(
            f"Unexpected error getting table {name} from database {database_name}: {str(e)}"
        )


def create_http_app():
    """Create FastAPI app for HTTP transport"""
    try:
        from fastapi import FastAPI, Request

        app = FastAPI(
            title="Glue MCP Server",
            description="MCP server for AWS Glue service",
            version="1.0.0",
        )

        @app.get("/health")
        async def health_check():
            """Health check endpoint for ALB"""
            # Get the actual tool count from FastMCP's tool manager
            tool_count = len(mcp._tool_manager._tools)
            return {
                "status": "healthy",
                "service": "glue-mcp-server",
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
                "service": "Glue MCP Server",
                "status": "running",
                "transport": "http",
                "endpoints": ["/health", "/mcp/glue"],
                "tools_available": tools_available,
            }

        @app.get("/mcp/glue")
        def mcp_root():
            """MCP root endpoint"""
            return {
                "jsonrpc": "2.0",
                "method": "initialize",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "glue-mcp-server", "version": "1.0.0"},
                },
            }

        @app.post("/mcp/glue")
        async def mcp_endpoint(request: Request):
            """MCP JSON-RPC endpoint using real tools"""
            request_data = {}
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
                                or f"Glue tool: {tool_name}",
                                "inputSchema": input_schema,
                            }
                        except Exception:
                            # Fallback if schema generation fails
                            tool_info = {
                                "name": tool_name,
                                "description": tool_obj.description
                                or f"Glue tool: {tool_name}",
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
                    "id": request_data.get("id", None),
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                }

        return app

    except ImportError as e:
        logger.error(f"FastAPI not available for HTTP transport: {e}")
        return None


# Start the MCP server
if __name__ == "__main__":
    try:
        logger.info("Starting Glue MCP server")
        # Debug info for troubleshooting
        logger.info(f"FastMCP version: {getattr(FastMCP, '__version__', 'unknown')}")
        logger.info(f"Number of registered tools: {len(getattr(mcp, '_tools', []))}")

        # Check transport mode via environment variable
        transport_mode = os.getenv("MCP_TRANSPORT", "stdio").lower()

        if transport_mode == "http":
            # HTTP transport for Docker deployment
            logger.info("Starting Glue MCP server with HTTP transport")

            app = create_http_app()
            if not app:
                sys.exit(1)

            # Get configuration from environment
            host = os.getenv("HOST", "0.0.0.0")  # nosec B104
            port = int(os.getenv("PORT", "8081"))

            # Start server with uvicorn
            import uvicorn

            uvicorn.run(app, host=host, port=port, log_level="info")
        else:
            # Default stdio transport
            logger.info("Starting Glue MCP server with stdio transport")
            mcp.run(transport="stdio")

    except Exception as e:
        logger.error(f"Failed to start Glue MCP server: {str(e)}")
        logger.error(traceback.format_exc())
        # Create a proper JSON error response
        error_response = {
            "error": str(e),
            "type": type(e).__name__,
            "message": "MCP server encountered an error",
            "details": {
                "server": "glue",
                "status": "failed",
                "traceback": traceback.format_exc(),
            },
        }
        print(json.dumps(error_response), file=sys.stderr)
        sys.exit(1)
