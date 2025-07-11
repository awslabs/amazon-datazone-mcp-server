# Amazon DataZone MCP Server

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](https://github.com/awslabs/amazon-datazone-mcp-server/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io/)

A high-performance Model Context Protocol (MCP) server that provides seamless integration with Amazon DataZone services. This server enables AI assistants and applications to interact with Amazon DataZone APIs through a standardized interface.

## Features

- **Complete Amazon DataZone API Coverage**: Access all major DataZone operations
- **Modular Architecture**: Well-organized, maintainable code structure
- **Type Safety**: Full TypeScript-style type hints for Python
- **Comprehensive Error Handling**: Detailed error messages and proper exception handling
- **Production Ready**: Robust logging, validation, and configuration management

### Supported Operations

| Module | Operations |
|--------|------------|
| **Domain Management** | Create domains, manage domain units, search, policy grants |
| **Project Management** | Create/manage projects, project profiles, memberships |
| **Data Management** | Assets, listings, subscriptions, form types, data sources |
| **Glossary** | Business glossaries, glossary terms |
| **Environment** | Environments, connections, blueprints |

## Configuration

Please follow the https://modelcontextprotocol.io/ for configure this MCP server via stdio.

## Available Tools

The Amazon DataZone MCP server provides **38 tools** organized into 5 categories:

### Domain Management
- `get_domain` - Retrieve domain information
- `create_domain` - Create a new domain
- `list_domain_units` - List domain units
- `create_domain_unit` - Create domain unit
- `list_domains` - List domains
- `add_entity_owner` - Add entity ownership
- `add_policy_grant` - Grant policies
- `search` - Search across DataZone
- `search_types` - Search typs across DataZone
- `get_user_profile` - Get user profile
- `search_user_profiles` - Search user profiles
- `search_group_profiles` - Search group profiles

### Project Management
- `create_project` - Create new project
- `get_project` - Get project details
- `list_projects` - List all projects
- `create_project_membership` - Add project members
- `list_project_profiles` - List project profiles
- `create_project_profile` - Create project profile
- `get_project_profile` - Get project profile
- `list_project_memberships` - List project memberships

### Glossary Management
- `create_glossary` - Create business glossary
- `create_glossary_term` - Create glossary term
- `get_glossary` - Get glossary details
- `get_glossary_term` - Get term details

### Data Management
- `get_asset` - Retrieve asset information
- `create_asset` - Create new asset
- `publish_asset` - Publish asset to catalog
- `get_listing` - Get asset listing
- `search_listings` - Search published assets
- `create_data_source` - Create data source
- `get_data_source` - Get data source
- `start_data_source_run` - Start data source run
- `create_subscription_request` - Request data subscription
- `accept_subscription_request` - Accept subscription
- `get_form_type` - Get metadata form type
- `create_form_type` - Create metadata form type
- `get_subscription` - Get subscription
- `list_data_sources` - List data sources


### Environment Management
- `list_environments` - List environments
- `create_connection` - Create environment connection
- `get_connection` - Get connection details
- `get_environment` - Get environment details
- `get_environment_blueprint` - Get environment blueprint
- `get_environment_blueprint_configuration` - Get environment blueprint configuration
- `list_connections` - List all connections
- `list_environment_blueprints` - List available blueprints
- `list_environment_blueprint_configurations` - List available blueprint configurations
- `list_environment_profiles` - List environment profiles

> **For detailed documentation** of each tool with parameters and examples, see our [Tool Reference](docs/TOOL_REFERENCE.md).

## Security Considerations

### Transport Mode Security

This MCP server supports two transport modes:

#### **stdio Transport (Recommended for Local Development)**
- **Default and most secure**: No network exposure
- **Use for**: Local development, Claude Desktop integration, direct MCP client usage
- **Security**: Zero network attack surface, only parent process can communicate

```bash
# Secure stdio mode (default)
python servers/datazone/server.py
```

#### **HTTP Transport (Use with Caution)**
- **Network exposure**: Binds to `127.0.0.1` (localhost only) by default
- **Use for**: Container deployments, integration testing, multi-service architectures
- **Security considerations**:
  - Only use in controlled environments
  - Default binding to localhost prevents remote access
  - Consider additional authentication for production use

```bash
# HTTP mode - localhost only (secure)
MCP_TRANSPORT=http python servers/datazone/server.py
```

### Security Best Practices

1. **Use stdio transport** for local development and MCP client integration
2. **Use HTTP transport** only when necessary (containers, health checks, etc.)
3. **Use Docker** for HTTP deployments to provide additional network isolation
4. **Implement additional authentication** for production HTTP deployments

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Disclaimer

**This is an unofficial, community-developed project and is not affiliated with, endorsed by, or supported by Amazon Web Services, Inc.**

- AWS and DataZone are trademarks of Amazon.com, Inc. or its affiliates
- This project provides a community-built interface to Amazon DataZone APIs
- Users are responsible for their own AWS credentials, costs, and compliance
- No warranty or support is provided - use at your own risk
- Always follow AWS security best practices when using this tool

For official Amazon DataZone documentation and support, visit [Amazon DataZone Documentation](https://docs.aws.amazon.com/datazone/).

## Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the protocol specification
- [Amazon DataZone](https://aws.amazon.com/datazone/) for the data governance platform
- The open-source community for inspiration and contributions
