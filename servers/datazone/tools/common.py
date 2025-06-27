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
