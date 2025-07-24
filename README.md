# Amazon DataZone MCP Server

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](https://github.com/awslabs/amazon-datazone-mcp-server/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io/)

A high-performance Model Context Protocol (MCP) server that provides seamless integration with Amazon DataZone services. This server enables AI assistants and applications to interact with Amazon DataZone APIs through a standardized interface.

## Features

- **Complete Amazon DataZone API Coverage**: Access all major DataZone operations
- **Type Safety**: Full type hints and validation
- **Production Ready**: Robust error handling and logging
- **MCP Compatible**: Works with any MCP-compatible client

### Supported Operations

| Module | Operations |
|--------|------------|
| **Domain Management** | Create domains, manage domain units, search, policy grants |
| **Project Management** | Create/manage projects, project profiles, memberships |
| **Data Management** | Assets, listings, subscriptions, form types, data sources |
| **Glossary** | Business glossaries, glossary terms |
| **Environment** | Environments, connections, blueprints |

## Installation

```bash
pip install amazon-datazone-mcp-server
```

## Configuration

Configure AWS credentials using the standard AWS methods:
- AWS CLI: `aws configure`
- Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`
- IAM roles or instance profiles

## Running the Server

The server uses **stdio transport** for secure communication with MCP clients:

```bash
amazon-datazone-mcp-server
```

### Integration with MCP Clients

Configure in your MCP client (e.g., Claude Desktop):

```json
{
  "name": "amazon-datazone-mcp-server",
  "command": "amazon-datazone-mcp-server"
}
```

## Available Tools

The server provides **38 tools** across 5 categories:

### Domain Management
- `get_domain`, `create_domain`, `list_domains`
- `list_domain_units`, `create_domain_unit`
- `add_entity_owner`, `add_policy_grant`
- `search`, `search_types`
- User/group profile management

### Project Management
- `create_project`, `get_project`, `list_projects`
- `create_project_membership`, `list_project_memberships`
- Project profile management

### Data Management
- Asset operations: `get_asset`, `create_asset`, `publish_asset`
- Listing operations: `get_listing`, `search_listings`
- Data source management: `create_data_source`, `start_data_source_run`
- Subscription management: request, accept, get subscriptions
- Form type management

### Glossary Management
- `create_glossary`, `get_glossary`
- `create_glossary_term`, `get_glossary_term`

### Environment Management
- Environment operations: `list_environments`, `get_environment`
- Connection management: `create_connection`, `get_connection`, `list_connections`
- Blueprint operations: list and get blueprints and configurations

**Each tool includes comprehensive parameter documentation and examples accessible through your MCP client.**

## License

Licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Disclaimer

**This is an unofficial, community-developed project and is not affiliated with, endorsed by, or supported by Amazon Web Services, Inc.**

- AWS and DataZone are trademarks of Amazon.com, Inc. or its affiliates
- Users are responsible for their own AWS credentials, costs, and compliance
- No warranty or support is provided - use at your own risk
- Always follow AWS security best practices

For official Amazon DataZone documentation, visit [Amazon DataZone Documentation](https://docs.aws.amazon.com/datazone/).
