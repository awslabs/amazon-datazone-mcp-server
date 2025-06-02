"""
Environment management tools for AWS DataZone.
"""
from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP
from .common import datazone_client, logger, ClientError

def register_tools(mcp: FastMCP):
    """Register environment management tools with the MCP server."""
    
    @mcp.tool()
    async def list_environments(
        domain_identifier: str,
        project_identifier: str,
        max_results: int = 50,
        next_token: str = None,
        aws_account_id: str = None,
        aws_account_region: str = None,
        environment_blueprint_identifier: str = None,
        environment_profile_identifier: str = None,
        name: str = None,
        provider: str = None,
        status: str = None
    ) -> Any:
        """
        Lists environments in Amazon DataZone.
        
        Args:
            domain_identifier (str): The identifier of the Amazon DataZone domain.
            project_identifier (str): The identifier of the Amazon DataZone project.
            max_results (int, optional): Maximum number of environments to return. Defaults to 50.
            next_token (str, optional): Token for pagination. Defaults to None.
            aws_account_id (str, optional): The identifier of the AWS account where you want to list environments.
            aws_account_region (str, optional): The AWS region where you want to list environments.
            environment_blueprint_identifier (str, optional): The identifier of the Amazon DataZone blueprint.
            environment_profile_identifier (str, optional): The identifier of the environment profile.
            name (str, optional): The name of the environment.
            provider (str, optional): The provider of the environment.
            status (str, optional): The status of the environments to list.
                Valid values: ACTIVE, CREATING, UPDATING, DELETING, CREATE_FAILED, UPDATE_FAILED,
                DELETE_FAILED, VALIDATION_FAILED, SUSPENDED, DISABLED, EXPIRED, DELETED, INACCESSIBLE
        
        Returns:
            Any: The API response containing environment details or None if an error occurs
        
        Example:
            >>> list_environments(
            ...     domain_identifier="dzd_4p9n6sw4qt9xgn",
            ...     project_identifier="prj_123456789",
            ...     status="ACTIVE"
            ... )
        """
        try:
            params = {
                "domainIdentifier": domain_identifier,
                "projectIdentifier": project_identifier,
                "maxResults": max_results
            }
            
            # Add optional parameters if provided
            if next_token:
                params["nextToken"] = next_token
            if aws_account_id:
                params["awsAccountId"] = aws_account_id
            if aws_account_region:
                params["awsAccountRegion"] = aws_account_region
            if environment_blueprint_identifier:
                params["environmentBlueprintIdentifier"] = environment_blueprint_identifier
            if environment_profile_identifier:
                params["environmentProfileIdentifier"] = environment_profile_identifier
            if name:
                params["name"] = name
            if provider:
                params["provider"] = provider
            if status:
                params["status"] = status
            
            response = datazone_client.list_environments(**params)
            return response
        except ClientError as e:
            raise Exception(f"Error listing environments: {e}")

    @mcp.tool()
    async def create_connection(
        domain_identifier: str,
        name: str,
        environment_identifier: str = None,
        aws_location: Dict[str, str] = None,
        description: str = None,
        client_token: str = None,
        props: Dict[str, Any] = None
    ) -> Any:
        """
        Creates a new connection in Amazon DataZone. A connection enables you to connect your resources
        (domains, projects, and environments) to external resources and services.

        This is specifically for creating DataZone connections and should be used in the DataZone MCP server.
        
        Args:
            domain_identifier (str): The ID of the domain where the connection is created.
                Pattern: ^dzd[-_][a-zA-Z0-9_-]{1,36}$
            name (str): The connection name.
                Length Constraints: Minimum length of 0. Maximum length of 64.
            environment_identifier (str, optional): The ID of the environment where the connection is created.
                Pattern: ^[a-zA-Z0-9_-]{1,36}$
            aws_location (Dict[str, str], optional): The location where the connection is created.
                Contains:
                    - accessRole (str): The access role for the connection
                    - awsAccountId (str): The AWS account ID
                    - awsRegion (str): The AWS region
                    - iamConnectionId (str): The IAM connection ID
            description (str, optional): A connection description.
                Length Constraints: Minimum length of 0. Maximum length of 128.
            client_token (str, optional): A unique, case-sensitive identifier to ensure idempotency.
            props (Dict[str, Any], optional): The connection properties.
                Type: ConnectionPropertiesInput object (Union type)
        
        Returns:
            Any: The API response containing:
                - connectionId (str): The ID of the created connection
                - description (str): The connection description
                - domainId (str): The domain ID
                - domainUnitId (str): The domain unit ID
                - environmentId (str): The environment ID
                - name (str): The connection name
                - physicalEndpoints (list): The physical endpoints of the connection
                - projectId (str): The project ID
                - props (dict): The connection properties
                - type (str): The connection type
        
        Example:
            >>> create_connection(
            ...     domain_identifier="dzd_4p9n6sw4qt9xgn",
            ...     name="MyConnection",
            ...     environment_identifier="env_123456789",
            ...     aws_location={
            ...         "accessRole": "arn:aws:iam::123456789012:role/DataZoneAccessRole",
            ...         "awsAccountId": "123456789012",
            ...         "awsRegion": "us-east-1",
            ...         "iamConnectionId": "iam-123456789"
            ...     },
            ...     description="Connection to external service"
            ... )
        """
        try:
            # Prepare the request parameters
            params = {
                "domainIdentifier": domain_identifier,
                "name": name
            }
            
            # Add optional parameters if provided
            if environment_identifier:
                params["environmentIdentifier"] = environment_identifier
            if aws_location:
                params["awsLocation"] = aws_location
            if description:
                params["description"] = description
            if client_token:
                params["clientToken"] = client_token
            if props:
                params["props"] = props
            
            response = datazone_client.create_connection(**params)
            return response
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            if error_code == "AccessDeniedException":
                raise Exception(f"Access denied while creating connection in domain {domain_identifier}: {error_message}")
            elif error_code == "ConflictException":
                raise Exception(f"Conflict while creating connection in domain {domain_identifier}: {error_message}")
            elif error_code == "ResourceNotFoundException":
                raise Exception(
                    f"Resource not found while creating connection in domain {domain_identifier}: {error_message}")
            elif error_code == "ServiceQuotaExceededException":
                raise Exception(
                    f"Service quota exceeded while creating connection in domain {domain_identifier}: {error_message}")
            elif error_code == "ValidationException":
                raise Exception(
                    f"Invalid parameters while creating connection in domain {domain_identifier}: {error_message}")
            else:
                raise Exception(f"Unexpected error creating connection in domain {domain_identifier}: {error_message}")

    @mcp.tool()
    async def get_connection(
        domain_identifier: str,
        identifier: str,
        with_secret: bool = False
    ) -> Any:
        """
        Gets a connection in Amazon DataZone. A connection enables you to connect your resources
        (domains, projects, and environments) to external resources and services.
        
        This is specifically for retrieving DataZone connections and should be used in the DataZone MCP server.
        
        Args:
            domain_identifier (str): The ID of the domain where the connection exists.
                Pattern: ^dzd[-_][a-zA-Z0-9_-]{1,36}$
            identifier (str): The ID of the connection to retrieve.
                Length Constraints: Minimum length of 0. Maximum length of 128.
            with_secret (bool, optional): Specifies whether to include connection secrets.
                Defaults to False.
        
        Returns:
            Any: The API response containing:
                - connectionId (str): The ID of the connection
                - description (str): The connection description
                - domainId (str): The domain ID
                - domainUnitId (str): The domain unit ID
                - environmentId (str): The environment ID
                - environmentUserRole (str): The environment user role
                - name (str): The connection name
                - physicalEndpoints (list): The physical endpoints of the connection
                - projectId (str): The project ID
                - props (dict): The connection properties
                - type (str): The connection type
                - connectionCredentials (dict, optional): If with_secret is True, includes:
                    - accessKeyId (str)
                    - expiration (str)
                    - secretAccessKey (str)
                    - sessionToken (str)
        
        Example:
            >>> get_connection(
            ...     domain_identifier="dzd_4p9n6sw4qt9xgn",
            ...     identifier="conn_123456789",
            ...     with_secret=True
            ... )
        """
        try:
            # Prepare the request parameters
            params = {
                "domainIdentifier": domain_identifier,
                "identifier": identifier
            }
            
            # Add with_secret parameter if True
            if with_secret:
                params["withSecret"] = with_secret
            
            response = datazone_client.get_connection(**params)
            return response
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            if error_code == "AccessDeniedException":
                raise Exception(f"Access denied while getting connection {identifier} in domain {domain_identifier}: {error_message}")
            elif error_code == "ResourceNotFoundException":
                raise Exception(f"Connection {identifier} not found in domain {domain_identifier}: {error_message}")
            elif error_code == "ValidationException":
                raise Exception(f"Invalid parameters while getting connection {identifier} in domain {domain_identifier}: {error_message}")
            else:
                raise Exception(f"Error getting connection {identifier} in domain {domain_identifier}: {error_message}")

    # @mcp.tool()
    # async def list_connections(
    #     domain_identifier: str,
    #     project_identifier: str,
    #     max_results: int = 50,
    #     next_token: str = None,
    #     environment_identifier: str = None,
    #     name: str = None,
    #     sort_by: str = None,
    #     sort_order: str = None,
    #     type: str = None
    # ) -> Dict[str, Any]:
    #     """
    #     Lists connections in Amazon DataZone.
        
    #     This is specifically for listing DataZone connections and should be used in the DataZone MCP server.
        
    #     Args:
    #         domain_identifier (str): The ID of the domain where you want to list connections
    #         project_identifier (str): The ID of the project where you want to list connections
    #         max_results (int, optional): Maximum number of connections to return (1-50, default: 50)
    #         next_token (str, optional): Token for pagination
    #         environment_identifier (str, optional): The ID of the environment where you want to list connections
    #         name (str, optional): The name of the connection to filter by (0-64 characters)
    #         sort_by (str, optional): How to sort the listed connections (valid: "NAME")
    #         sort_order (str, optional): Sort order (valid: "ASCENDING" or "DESCENDING")
    #         type (str, optional): The type of connection to filter by (valid: ATHENA, BIGQUERY, DATABRICKS, etc.)
        
    #     Returns:
    #         Dict[str, Any]: The list of connections including:
    #             - items: Array of connection summaries
    #             - nextToken: Token for pagination if more results are available
    #     """
    #     try:
    #         # Prepare the request parameters
    #         params = {
    #             "domainIdentifier": domain_identifier,
    #             "projectIdentifier": project_identifier,
    #             "maxResults": min(max_results, 50)  # Ensure maxResults is within valid range
    #         }
            
    #         # Add optional parameters if provided
    #         if next_token:
    #             params["nextToken"] = next_token
    #         if environment_identifier:
    #             params["environmentIdentifier"] = environment_identifier
    #         if name:
    #             params["name"] = name
    #         if sort_by:
    #             params["sortBy"] = sort_by
    #         if sort_order:
    #             params["sortOrder"] = sort_order
    #         if type:
    #             params["type"] = type
            
    #         response = datazone_client.list_connections(**params)
    #         return response
    #     except ClientError as e:
    #         error_code = e.response["Error"]["Code"]
    #         error_message = e.response["Error"]["Message"]
            
    #         if error_code == "AccessDeniedException":
    #             raise Exception(f"Access denied while listing connections in domain {domain_identifier}: {error_message}")
    #         elif error_code == "ValidationException":
    #             raise Exception(f"Invalid parameters while listing connections in domain {domain_identifier}: {error_message}")
    #         else:
    #             raise Exception(f"Unexpected error listing connections in domain {domain_identifier}: {error_message}")

    # @mcp.tool()
    # async def list_environment_blueprints(
    #     domain_identifier: str,
    #     managed: bool = None,
    #     max_results: int = 50,
    #     name: str = None,
    #     next_token: str = None
    # ) -> Dict[str, Any]:
    #     """
    #     Lists environment blueprints in an Amazon DataZone domain.
        
    #     Args:
    #         domain_identifier (str): The ID of the domain where the blueprints are listed
    #             Pattern: ^dzd[-_][a-zA-Z0-9_-]{1,36}$
    #         managed (bool, optional): Specifies whether to list only managed blueprints
    #         max_results (int, optional): Maximum number of blueprints to return (1-50, default: 50)
    #         name (str, optional): Filter blueprints by name (1-64 characters)
    #             Pattern: ^[\\w -]+$
    #         next_token (str, optional): Token for pagination (1-8192 characters)
        
    #     Returns:
    #         Dict containing:
    #             - items: List of environment blueprints, each containing:
    #                 - id: Blueprint identifier
    #                 - name: Blueprint name
    #                 - description: Blueprint description
    #                 - provider: Blueprint provider
    #                 - provisioning_properties: Blueprint provisioning properties
    #                 - created_at: Creation timestamp
    #                 - updated_at: Last update timestamp
    #             - next_token: Token for pagination if more results are available
    #     """
    #     try:
    #         logger.info(f"Listing environment blueprints in domain {domain_identifier}")
            
    #         # Prepare request parameters
    #         params = {
    #             'domainIdentifier': domain_identifier,
    #             'maxResults': min(max_results, 50)  # Ensure maxResults is within valid range
    #         }
            
    #         # Add optional parameters
    #         if managed is not None:
    #             params['managed'] = managed
    #         if name:
    #             params['name'] = name
    #         if next_token:
    #             params['nextToken'] = next_token
            
    #         # List the environment blueprints
    #         response = datazone_client.list_environment_blueprints(**params)
            
    #         # Format the response
    #         result = {
    #             'items': [],
    #             'next_token': response.get('nextToken')
    #         }
            
    #         # Format each blueprint
    #         for blueprint in response.get('items', []):
    #             formatted_blueprint = {
    #                 'id': blueprint.get('id'),
    #                 'name': blueprint.get('name'),
    #                 'description': blueprint.get('description'),
    #                 'provider': blueprint.get('provider'),
    #                 'provisioning_properties': blueprint.get('provisioningProperties'),
    #                 'created_at': blueprint.get('createdAt'),
    #                 'updated_at': blueprint.get('updatedAt')
    #             }
    #             result['items'].append(formatted_blueprint)
            
    #         logger.info(f"Successfully listed {len(result['items'])} environment blueprints in domain {domain_identifier}")
    #         return result
            
    #     except ClientError as e:
    #         error_code = e.response['Error']['Code']
    #         if error_code == 'AccessDeniedException':
    #             logger.error(f"Access denied while listing environment blueprints in domain {domain_identifier}")
    #             raise Exception(f"Access denied while listing environment blueprints in domain {domain_identifier}")
    #         elif error_code == 'ResourceNotFoundException':
    #             logger.error(f"Domain {domain_identifier} not found while listing environment blueprints")
    #             raise Exception(f"Domain {domain_identifier} not found while listing environment blueprints")
    #         elif error_code == 'ValidationException':
    #             logger.error(f"Invalid parameters for listing environment blueprints in domain {domain_identifier}")
    #             raise Exception(f"Invalid parameters for listing environment blueprints in domain {domain_identifier}")
    #         else:
    #             logger.error(f"Error listing environment blueprints in domain {domain_identifier}: {str(e)}")
    #             raise Exception(f"Error listing environment blueprints in domain {domain_identifier}: {str(e)}")
    #     except Exception as e:
    #         logger.error(f"Unexpected error listing environment blueprints in domain {domain_identifier}: {str(e)}")
    #         raise Exception(f"Unexpected error listing environment blueprints in domain {domain_identifier}: {str(e)}")

    # Return the decorated functions for testing purposes
    return {
        "list_environments": list_environments,
        "create_connection": create_connection,
        "get_connection": get_connection,
        # "list_connections": list_connections,
        # "list_environment_blueprints": list_environment_blueprints
    } 