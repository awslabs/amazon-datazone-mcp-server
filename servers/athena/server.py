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
import time
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


def initialize_aws_session():
    """Initialize AWS session with proper credential handling (no credential exposure)"""
    try:
        # Check for local development environment using generic environment variable
        # Use MCP_LOCAL_DEV=true to indicate local development instead of hardcoded key patterns
        is_local_dev = os.environ.get("MCP_LOCAL_DEV", "").lower() == "true"

        if (
            is_local_dev
            and os.environ.get("AWS_ACCESS_KEY_ID")
            and os.environ.get("AWS_SECRET_ACCESS_KEY")
            and os.environ.get("AWS_SESSION_TOKEN")
        ):
            logger.info(
                "Using AWS credentials from environment variables (local development)"
            )
            session = boto3.Session(
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
                region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            )
            # Get account ID dynamically from STS
            try:
                sts_client = session.client("sts")
                account_id = sts_client.get_caller_identity()["Account"]
                logger.info(f"Retrieved account ID from STS: {account_id}")
                return session, account_id
            except Exception as e:
                logger.warning(f"Could not retrieve account ID from STS: {e}")
                return session, os.environ.get("AWS_ACCOUNT_ID", "unknown")

        # For AWS deployment, retrieve from Secrets Manager
        logger.info(
            "Running in AWS environment - retrieving credentials from Secrets Manager..."
        )
        secrets_client = boto3.client("secretsmanager", region_name="us-east-1")

        secret_name = os.getenv(
            "AWS_SECRET_NAME", "datazone-mcp-server/aws-credentials"
        )  # pragma: allowlist secret
        logger.info(f"Retrieving credentials from secret: {secret_name}")

        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_value = json.loads(response["SecretString"])

        logger.info(
            f"Successfully retrieved credentials from Secrets Manager for account: {secret_value.get('ACCOUNT_ID', 'unknown')}"
        )
        session = boto3.Session(
            aws_access_key_id=secret_value["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=secret_value["AWS_SECRET_ACCESS_KEY"],
            aws_session_token=secret_value["AWS_SESSION_TOKEN"],
            region_name=secret_value["AWS_DEFAULT_REGION"],
        )
        return session, secret_value.get("ACCOUNT_ID", "unknown")

    except Exception as e:
        logger.error(f"Failed to retrieve credentials from Secrets Manager: {e}")
        logger.warning("Falling back to default AWS credentials")
        # Try to get account ID from default session
        try:
            default_session = boto3.Session()
            sts_client = default_session.client("sts")
            account_id = sts_client.get_caller_identity()["Account"]
            logger.info(f"Retrieved account ID from default credentials: {account_id}")
            return default_session, account_id
        except Exception as sts_e:
            logger.warning(
                f"Could not retrieve account ID from default credentials: {sts_e}"
            )
            return boto3.Session(), os.environ.get("AWS_ACCOUNT_ID", "unknown")


# Initialize AWS session securely
session, account_id = initialize_aws_session()

# Initialize FastMCP server
mcp = FastMCP("athena")

# Initialize boto3 clients with explicit credentials
try:
    athena_client = session.client("athena")
    s3_client = session.client("s3")
    logger.info(f"Successfully initialized Athena clients for account: {account_id}")

    # Verify credentials with STS get_caller_identity
    try:
        sts_client = session.client("sts")
        identity = sts_client.get_caller_identity()
        actual_account = identity.get("Account", "unknown")
        user_arn = identity.get("Arn", "unknown")
        logger.info(
            f"STS VERIFICATION SUCCESS - Athena MCP connected to AWS Account: {actual_account}"
        )
        logger.info(f"STS Identity ARN: {user_arn}")

        # Log warning if account mismatch
        if actual_account != account_id and account_id != "unknown":
            logger.warning(
                f"ACCOUNT MISMATCH - Expected: {account_id}, Actual: {actual_account}"
            )
        else:
            logger.info(
                f"ACCOUNT MATCH CONFIRMED - Using correct account: {actual_account}"
            )

    except Exception as sts_error:
        logger.error(
            f"STS VERIFICATION FAILED - Cannot verify AWS credentials: {sts_error}"
        )

except Exception as e:
    logger.error(f"Failed to initialize Athena clients: {str(e)}")
    # Don't raise - allow server to start without credentials for testing
    athena_client = None
    s3_client = None

logger.info("Creating FastMCP server for Athena tool...")

logger.info("Initializing AWS clients...")
# Initialize boto3 clients (don't call APIs during module load)
try:
    datazone_client = session.client("datazone")
    sts_client = session.client("sts")

    # Get region for logging (this doesn't require credentials)
    region = session.region_name or "us-east-1"
    logger.info(f"AWS region: {region}, Clients initialized")
except Exception as e:
    logger.error(f"Failed to initialize AWS clients: {str(e)}")
    # Don't raise - allow server to start without credentials for testing
    datazone_client = None
    sts_client = None


@mcp.tool()
async def athena_execute_sql_query(
    domain_identifier: str,
    project_identifier: str,
    sql_query: str,
    database_name: Optional[str] = None,
    max_results: int = 100,
) -> Any:
    """
    Executes a SQL query against data in a DataZone project environment.

    This tool allows the LLM to translate natural language queries into SQL and execute them.
    The LLM should generate appropriate SQL based on the user's request.

    Args:
        domain_identifier (str): The ID of the domain (e.g., "dzd_bvgcinc6awq8kn")
        project_identifier (str): The ID of the project with access to the data
        sql_query (str): The SQL query to execute (generated by the LLM from natural language)
        database_name (str, optional): The specific database name to query
        max_results (int, optional): Maximum number of results to return (default: 100)

    Returns:
        Any: The query results including:
            - Column names and types
            - Result rows
            - Execution statistics
    """
    try:
        logger.info(f"Executing SQL query for project {project_identifier}")

        # List all environments for the project
        if not datazone_client:
            raise Exception("DataZone client not initialized")
        environments = datazone_client.list_environments(
            domainIdentifier=domain_identifier, projectIdentifier=project_identifier
        )

        # Find an active environment
        active_env = None
        for env in environments.get("items", []):
            if env.get("status") == "ACTIVE":
                active_env = env
                break

        if not active_env:
            raise Exception(
                f"No active environment found for project {project_identifier}"
            )

        # List connections for the project to find the Athena connection
        connections = datazone_client.list_connections(
            domainIdentifier=domain_identifier,
            projectIdentifier=project_identifier,
            type="ATHENA",
        )

        athena_connection = None
        for conn in connections.get("items", []):
            if conn.get("type") == "ATHENA":
                athena_connection = conn
                break

        if not athena_connection:
            raise Exception(
                f"No Athena connection found for project {project_identifier}"
            )

        # Get the workgroup name from the Athena connection properties
        workgroup = (
            athena_connection.get("props", {})
            .get("athenaProperties", {})
            .get("workgroupName")
        )
        if not workgroup:
            raise Exception("No Athena workgroup found in connection properties")

        # Prepare query execution parameters
        if not sts_client:
            raise Exception("STS client not initialized")
        account_id = sts_client.get_caller_identity()["Account"]
        region = session.region_name

        query_params = {
            "QueryString": sql_query,
            "WorkGroup": workgroup,
            "ResultConfiguration": {
                "OutputLocation": f"s3://aws-athena-query-results-{account_id}-{region}/"
            },
        }

        # Add database name if provided
        if database_name:
            query_params["QueryExecutionContext"] = {"Database": database_name}

        # Start query execution
        logger.info(f"Starting query execution with workgroup {workgroup}")
        if not athena_client:
            raise Exception("Athena client not initialized")
        query_execution = athena_client.start_query_execution(**query_params)
        query_execution_id = query_execution["QueryExecutionId"]

        # Wait for query to complete
        state = "RUNNING"
        max_wait_time = 300  # 5 minutes timeout
        start_time = time.time()
        response = None

        while (
            state in ["RUNNING", "QUEUED"]
            and (time.time() - start_time) < max_wait_time
        ):
            response = athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            state = response["QueryExecution"]["Status"]["State"]

            if state == "FAILED":
                error = response["QueryExecution"]["Status"].get(
                    "StateChangeReason", "Unknown error"
                )
                raise Exception(f"Query execution failed: {error}")
            elif state == "CANCELLED":
                raise Exception("Query execution was cancelled")
            elif state == "SUCCEEDED":
                break

            time.sleep(1)

        if state not in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            raise Exception("Query execution timed out")

        # Ensure we have a valid response
        if not response:
            raise Exception("Query execution response not available")

        # Get query results
        logger.info("Query execution completed, fetching results")
        if not athena_client:
            raise Exception("Athena client not initialized")
        results = athena_client.get_query_results(
            QueryExecutionId=query_execution_id, MaxResults=max_results
        )

        # Format the results
        formatted_results = {
            "columns": [],
            "rows": [],
            "execution_time_ms": response["QueryExecution"]["Statistics"][
                "TotalExecutionTimeInMillis"
            ],
            "data_scanned_bytes": response["QueryExecution"]["Statistics"][
                "DataScannedInBytes"
            ],
        }

        # Extract column information
        for column in results["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]:
            formatted_results["columns"].append(
                {"name": column["Name"], "type": column["Type"]}
            )

        # Extract row data (skip the header row)
        for row in results["ResultSet"]["Rows"][1:]:
            formatted_row = []
            for data in row["Data"]:
                formatted_row.append(data.get("VarCharValue", ""))
            formatted_results["rows"].append(formatted_row)

        logger.info(
            f"Query completed successfully. Returned {len(formatted_results['rows'])} rows"
        )
        return formatted_results

    except Exception as e:
        logger.error(f"Error executing Athena SQL query: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"Athena SQL query failed: {str(e)}")


@mcp.tool()
async def athena_describe_available_tables(
    database_name: str,
    workgroup: Optional[str] = None,
    catalog_name: Optional[str] = None,
    max_results: int = 50,
    next_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Describes the available tables in an Athena database.

    Args:
        database_name (str): The name of the database to describe tables from
        workgroup (str, optional): The name of the workgroup to use
        catalog_name (str, optional): The name of the data catalog
        max_results (int, optional): Maximum number of tables to return (default: 50)
        next_token (str, optional): Token for pagination

    Returns:
        Dict[str, Any]: A dictionary containing:
            - tables: List of table metadata including:
                - name: Table name
                - type: Table type
                - create_time: Creation timestamp
                - last_access_time: Last access timestamp
                - parameters: Table parameters
                - columns: List of column information
            - next_token: Token for pagination if more results are available
    """
    try:
        logger.info(f"Describing tables in database {database_name}")

        # Prepare the request parameters
        params = {"DatabaseName": database_name, "MaxResults": max_results}

        # Add optional parameters if provided
        if workgroup:
            params["WorkGroup"] = workgroup
        if catalog_name:
            params["CatalogName"] = catalog_name
        if next_token:
            params["NextToken"] = next_token

        # Get table list
        if not athena_client:
            raise Exception("Athena client not initialized")
        response = athena_client.list_table_metadata(**params)

        # Format the response
        formatted_tables = []
        for table in response.get("TableMetadataList", []):
            table_info = {
                "name": table.get("Name"),
                "type": table.get("TableType"),
                "create_time": table.get("CreateTime"),
                "last_access_time": table.get("LastAccessTime"),
                "parameters": table.get("Parameters", {}),
                "columns": [],
            }

            # Get column information
            for column in table.get("Columns", []):
                table_info["columns"].append(
                    {
                        "name": column.get("Name"),
                        "type": column.get("Type"),
                        "comment": column.get("Comment"),
                    }
                )

            formatted_tables.append(table_info)

        result = {"tables": formatted_tables, "next_token": response.get("NextToken")}

        logger.info(f"Found {len(formatted_tables)} tables in database {database_name}")
        return result

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_msg = f"Error describing tables: {str(e)}"
        logger.error(error_msg)
        if error_code == "InvalidRequestException":
            raise Exception(f"Invalid request: {str(e)}")
        elif error_code == "MetadataException":
            raise Exception(f"Metadata error: {str(e)}")
        else:
            raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error describing tables: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


# Start the MCP server
if __name__ == "__main__":
    try:
        logger.info("Starting Athena MCP server")
        # Debug info for troubleshooting
        logger.info(f"FastMCP version: {getattr(FastMCP, '__version__', 'unknown')}")

        # Properly count registered tools
        tool_count = 0
        try:
            if hasattr(mcp, "_tool_manager") and hasattr(mcp._tool_manager, "_tools"):
                tool_count = len(mcp._tool_manager._tools)
            elif hasattr(mcp, "tools"):
                tool_count = len(getattr(mcp, "tools", []))
            else:
                tool_count = 2  # We know there are 2 tools defined
        except Exception as e:
            logger.warning(f"Could not count tools: {e}")
            tool_count = 2

        logger.info(f"Number of registered tools: {tool_count}")
        if tool_count == 0:
            logger.warning(
                "No tools registered! This may indicate a FastMCP version compatibility issue."
            )
            logger.info(
                "Available tools should be: athena_execute_sql_query, athena_describe_available_tables"
            )

        # Start Athena MCP server with stdio transport only
        logger.info("Starting Athena MCP server with stdio transport")
        mcp.run(transport="stdio")

    except Exception as e:
        logger.error(f"Failed to start Athena MCP server: {str(e)}")
        logger.error(traceback.format_exc())
        # Create a proper JSON error response
        error_response = {
            "error": str(e),
            "type": type(e).__name__,
            "message": "MCP server encountered an error",
            "details": {
                "server": "athena",
                "status": "failed",
                "traceback": traceback.format_exc(),
            },
        }
        print(json.dumps(error_response), file=sys.stderr)
        sys.exit(1)
