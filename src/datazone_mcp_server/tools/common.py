"""
Common utilities, imports, and constants for DataZone MCP Server tools.
"""

from typing import Any, List, Dict, Optional
import logging
import boto3
from botocore.exceptions import ClientError
import httpx

# Constants
USER_AGENT = "datazone-app/1.0"

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize boto3 client
datazone_client = boto3.client("datazone")
