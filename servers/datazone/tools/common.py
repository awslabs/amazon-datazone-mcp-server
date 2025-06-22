"""
Common utilities, imports, and constants for DataZone MCP Server tools.
"""

import logging
from typing import Any, Dict, List, Optional

import boto3
import httpx
from botocore.exceptions import ClientError

# Constants
USER_AGENT = "datazone-app/1.0"

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LazyDataZoneClient:
    """Lazy-loading wrapper for DataZone client to avoid import-time failures"""
    
    def __init__(self):
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                self._client = boto3.client("datazone")
            except Exception as e:
                logger.warning(f"Failed to initialize DataZone client: {e}")
                # Return a mock client that raises meaningful errors
                raise RuntimeError(f"DataZone client not available: {e}")
        return self._client
    
    def __getattr__(self, name):
        """Delegate all method calls to the actual client"""
        client = self._get_client()
        return getattr(client, name)

# Initialize the lazy client
datazone_client = LazyDataZoneClient()
