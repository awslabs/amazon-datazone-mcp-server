"""
Project management tools for AWS DataZone.
"""
from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP
from .common import datazone_client, logger, ClientError, httpx, USER_AGENT

def register_tools(mcp: FastMCP):
    """Register project management tools with the MCP server."""
    
    @mcp.tool()
    async def create_project(
        domain_identifier: str,
        name: str,
        description: str = "",
        domain_unit_id: str = None,
        glossary_terms: List[str] = None,
        project_profile_id: str = None,
        user_parameters: List[Dict[str, Any]] = None
    ) -> Any:
        """
        Creates a new project in an AWS DataZone domain.
        
        Args:
            domain_identifier (str): The ID of the domain where the project will be created
            name (str): The name of the project (required)
            description (str, optional): The description of the project
            domain_unit_id (str, optional): The ID of the domain unit where the project will be created
            glossary_terms (List[str], optional): List of glossary terms that can be used in the project
            project_profile_id (str, optional): The ID of the project profile
            user_parameters (List[Dict[str, Any]], optional): The user parameters of the project
        
        Returns:
            Any: The API response containing the created project details
        """
        try:
            # Prepare the request parameters
            params = {
                "name": name,
                "description": description
            }
            
            # Add optional parameters if provided
            if domain_unit_id:
                params["domainUnitId"] = domain_unit_id
            if glossary_terms:
                params["glossaryTerms"] = glossary_terms
            if project_profile_id:
                params["projectProfileId"] = project_profile_id
            if user_parameters:
                params["userParameters"] = user_parameters

            response = datazone_client.create_project(
                domainIdentifier=domain_identifier,
                **params
            )
            return response
        except ClientError as e:
            raise Exception(f"Error creating project in domain {domain_identifier}: {e}")

    @mcp.tool()
    async def get_project(
        domain_identifier: str,
        project_identifier: str
    ) -> Any:
        """
        Retrieves detailed information about a specific project in Amazon DataZone.
        
        Args:
            domain_identifier (str): The ID of the domain containing the project
            project_identifier (str): The ID of the project to retrieve
        
        Returns:
            Any: The API response containing project details including:
                - Basic info (name, description, ID)
                - Timestamps (createdAt, lastUpdatedAt)
                - Domain IDs (domainId, domainUnitId)
                - Project status and profile
                - Environment deployment details
                - User parameters
                - Glossary terms
                - Failure reasons (if any)
        """
        try:
            response = datazone_client.get_project(
                domainIdentifier=domain_identifier,
                identifier=project_identifier
            )
            return response
        except ClientError as e:
            raise Exception(f"Error getting project {project_identifier} in domain {domain_identifier}: {e}")

    @mcp.tool()
    async def list_projects(
        domain_identifier: str,
        max_results: int = 50,
        next_token: str = None,
        name: str = None,
        user_identifier: str = None,
        group_identifier: str = None
    ) -> Any:
        """
        Lists projects in an AWS DataZone domain with optional filtering and pagination.
        
        Args:
            domain_identifier (str): The identifier of the domain
            max_results (int, optional): Maximum number of projects to return (1-50, default: 50)
            next_token (str, optional): Token for pagination
            name (str, optional): Filter projects by name
            user_identifier (str, optional): Filter projects by user
            group_identifier (str, optional): Filter projects by group
        
        Returns:
            Any: The API response containing the list of projects
        """
        try:
            # Prepare the request parameters
            params = {
                "domainIdentifier": domain_identifier,
                "maxResults": min(max_results, 50)  # Ensure maxResults is within valid range
            }
            
            # Add optional parameters if provided
            if next_token:
                params["nextToken"] = next_token
            if name:
                params["name"] = name
            if user_identifier:
                params["userIdentifier"] = user_identifier
            if group_identifier:
                params["groupIdentifier"] = group_identifier

            response = datazone_client.list_projects(**params)
            return response
        except ClientError as e:
            raise Exception(f"Error listing projects in domain {domain_identifier}: {e}")

    # @mcp.tool()
    # async def create_project_membership(domainIdentifier: str, projectIdentifier: str, designation: str, memberIdentifier: str) -> Any:
    #     """
    #     Make a request to the AWS DataZone CreateProjectMembership API.

    #     Args:
    #         domainIdentifier (str): The identifier of the domain.
    #         projectIdentifier (str): The identifier of the project.
    #         designation (str): The designation of the member.
    #         memberIdentifier (str): The identifier of the member.
    #     """
    #     headers = {
    #         "User-Agent": USER_AGENT,
    #         "Accept": "application/json",
    #     }

    #     async with httpx.AsyncClient() as client:
    #         try: 
    #             response = await client.post(
    #                 f"https://{domainIdentifier}.datazone.aws.dev/v2/domains/{domainIdentifier}/projects/{projectIdentifier}/createMembership",
    #                 headers=headers,
    #                 json={
    #                     "designation": designation,
    #                     "member": {
    #                         "identifier": memberIdentifier
    #                     }
    #                 }
    #             )
    #             response.raise_for_status()
    #             return response.json()
    #         except httpx.HTTPStatusError as e:
    #             raise Exception(f"Failed to create project membership: {e}")

    # @mcp.tool()
    # async def list_project_profiles(
    #     domain_identifier: str,
    #     max_results: int = 50,
    #     next_token: str = None
    # ) -> Any:
    #     """
    #     Lists all project profiles available in an AWS DataZone domain.
        
    #     Args:
    #         domain_identifier (str): The ID of the domain
    #         max_results (int, optional): Maximum number of profiles to return (1-50, default: 50)
    #         next_token (str, optional): Token for pagination
        
    #     Returns:
    #         Any: The API response containing the list of project profiles
    #     """
    #     try:
    #         # Prepare the request parameters
    #         params = {
    #             "domainIdentifier": domain_identifier,
    #             "maxResults": min(max_results, 50)  # Ensure maxResults is within valid range
    #         }
            
    #         # Add optional next token if provided
    #         if next_token:
    #             params["nextToken"] = next_token

    #         response = datazone_client.list_project_profiles(**params)
    #         return response
    #     except ClientError as e:
    #         raise Exception(f"Error listing project profiles in domain {domain_identifier}: {e}")

    # @mcp.tool()
    # async def create_project_profile(
    #     domain_identifier: str,
    #     name: str,
    #     description: str = None,
    #     domain_unit_identifier: str = None,
    #     environment_configurations: List[Dict[str, Any]] = None,
    #     status: str = "ENABLED"
    # ) -> Dict[str, Any]:
    #     """
    #     Creates a new project profile in Amazon DataZone.
        
    #     Args:
    #         domain_identifier (str): The ID of the domain where the project profile will be created
    #             Pattern: ^dzd[-_][a-zA-Z0-9_-]{1,36}$
    #         name (str): The name of the project profile (1-64 characters)
    #             Pattern: ^[\\w -]+$
    #         description (str, optional): Description of the project profile (0-2048 characters)
    #         domain_unit_identifier (str, optional): The ID of the domain unit where the project profile will be created
    #             Pattern: ^[a-z0-9_-]+$
    #         environment_configurations (List[Dict[str, Any]], optional): Environment configurations for the project profile
    #             Each configuration should include:
    #                 - awsAccount: AWS account details
    #                 - awsRegion: AWS region details
    #                 - configurationParameters: Configuration parameters
    #                 - deploymentMode: Deployment mode
    #                 - deploymentOrder: Deployment order
    #                 - description: Environment description
    #                 - environmentBlueprintId: Environment blueprint ID
    #                 - id: Environment ID
    #                 - name: Environment name
    #         status (str, optional): The status of the project profile (ENABLED or DISABLED, default: ENABLED)
        
    #     Returns:
    #         Dict containing:
    #             - id: Project profile identifier
    #             - name: Project profile name
    #             - description: Project profile description
    #             - domain_id: Domain ID
    #             - domain_unit_id: Domain unit ID
    #             - environment_configurations: Environment configurations
    #             - status: Project profile status
    #             - created_at: Creation timestamp
    #             - created_by: Creator information
    #             - last_updated_at: Last update timestamp
    #     """
    #     try:
    #         logger.info(f"Creating project profile '{name}' in domain {domain_identifier}")
            
    #         # Prepare request parameters
    #         params = {
    #             'domainIdentifier': domain_identifier,
    #             'name': name,
    #             'status': status
    #         }
            
    #         # Add optional parameters
    #         if description:
    #             params['description'] = description
    #         if domain_unit_identifier:
    #             params['domainUnitIdentifier'] = domain_unit_identifier
    #         if environment_configurations:
    #             params['environmentConfigurations'] = environment_configurations
            
    #         # Create the project profile
    #         response = datazone_client.create_project_profile(**params)
            
    #         # Format the response
    #         result = {
    #             'id': response.get('id'),
    #             'name': response.get('name'),
    #             'description': response.get('description'),
    #             'domain_id': response.get('domainId'),
    #             'domain_unit_id': response.get('domainUnitId'),
    #             'environment_configurations': response.get('environmentConfigurations', []),
    #             'status': response.get('status'),
    #             'created_at': response.get('createdAt'),
    #             'created_by': response.get('createdBy'),
    #             'last_updated_at': response.get('lastUpdatedAt')
    #         }
            
    #         logger.info(f"Successfully created project profile '{name}' in domain {domain_identifier}")
    #         return result
            
    #     except ClientError as e:
    #         error_code = e.response['Error']['Code']
    #         if error_code == 'AccessDeniedException':
    #             logger.error(f"Access denied while creating project profile '{name}' in domain {domain_identifier}")
    #             raise Exception(f"Access denied while creating project profile '{name}' in domain {domain_identifier}")
    #         elif error_code == 'ConflictException':
    #             logger.error(f"Project profile '{name}' already exists in domain {domain_identifier}")
    #             raise Exception(f"Project profile '{name}' already exists in domain {domain_identifier}")
    #         elif error_code == 'ResourceNotFoundException':
    #             logger.error(f"Domain or domain unit not found while creating project profile '{name}' in domain {domain_identifier}")
    #             raise Exception(f"Domain or domain unit not found while creating project profile '{name}' in domain {domain_identifier}")
    #         elif error_code == 'ServiceQuotaExceededException':
    #             logger.error(f"Service quota exceeded while creating project profile '{name}' in domain {domain_identifier}")
    #             raise Exception(f"Service quota exceeded while creating project profile '{name}' in domain {domain_identifier}")
    #         elif error_code == 'ValidationException':
    #             logger.error(f"Invalid parameters for creating project profile '{name}' in domain {domain_identifier}")
    #             raise Exception(f"Invalid parameters for creating project profile '{name}' in domain {domain_identifier}")
    #         else:
    #             logger.error(f"Error creating project profile '{name}' in domain {domain_identifier}: {str(e)}")
    #             raise Exception(f"Error creating project profile '{name}' in domain {domain_identifier}: {str(e)}")
    #     except Exception as e:
    #         logger.error(f"Unexpected error creating project profile '{name}' in domain {domain_identifier}: {str(e)}")
    #         raise Exception(f"Unexpected error creating project profile '{name}' in domain {domain_identifier}: {str(e)}")

    # Return the decorated functions for testing purposes
    return {
        "create_project": create_project,
        "get_project": get_project,
        "list_projects": list_projects,
        # "create_project_membership": create_project_membership,
        # "list_project_profiles": list_project_profiles,
        # "create_project_profile": create_project_profile
    } 