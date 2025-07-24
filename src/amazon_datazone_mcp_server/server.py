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

import boto3

# Import the real MCP tools
from mcp.server.fastmcp import FastMCP

from .tools import (
    data_management,
    domain_management,
    environment,
    glossary,
    project_management,
)

# configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
                logger.info("Successfully retrieved account ID from STS")
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
        logger.info("Retrieving credentials from Secrets Manager")

        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_value = json.loads(response["SecretString"])

        logger.info("Successfully retrieved credentials from Secrets Manager")
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
            logger.info("Successfully retrieved account ID from default credentials")
            return default_session, account_id
        except Exception as sts_e:
            logger.warning(
                f"Could not retrieve account ID from default credentials: {sts_e}"
            )
            return boto3.Session(), os.environ.get("AWS_ACCOUNT_ID", "unknown")


def create_mcp_server():
    """Create MCP server with real DataZone tools"""
    # Initialize AWS session securely
    session, account_id = initialize_aws_session()

    # Initialize FastMCP server
    mcp = FastMCP("datazone")

    # Initialize boto3 client with session
    try:
        session.client("datazone")  # Initialize client for verification only
        logger.info("Successfully initialized DataZone client")

        # Verify credentials with STS get_caller_identity
        try:
            sts_client = session.client("sts")
            identity = sts_client.get_caller_identity()
            actual_account = identity.get("Account", "unknown")
            logger.info("STS VERIFICATION SUCCESS - DataZone MCP connected to AWS")
            logger.info("STS Identity verified successfully")

            # Log warning if account mismatch
            if actual_account != account_id and account_id != "unknown":
                logger.warning(
                    "ACCOUNT MISMATCH - Expected and actual account IDs do not match"
                )
            else:
                logger.info("ACCOUNT MATCH CONFIRMED - Using correct account")

        except Exception as sts_error:
            logger.error(
                f"STS VERIFICATION FAILED - Cannot verify AWS credentials: {sts_error}"
            )

    except Exception as e:
        logger.error(f"Failed to initialize DataZone client: {str(e)}")
        # Don't raise - allow server to start without credentials for testing
        pass

    # Register all the real tools
    domain_management.register_tools(mcp)
    data_management.register_tools(mcp)
    project_management.register_tools(mcp)
    environment.register_tools(mcp)
    glossary.register_tools(mcp)

    return mcp


def main():
    """Entry point for console script."""
    try:
        # Start DataZone MCP server with stdio transport only
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
