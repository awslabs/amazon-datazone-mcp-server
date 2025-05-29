# AWS DataZone MCP Server

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io/)

A high-performance Model Context Protocol (MCP) server that provides seamless integration with AWS DataZone services. This server enables AI assistants and applications to interact with AWS DataZone APIs through a standardized interface.

## 🚀 Features

- **Complete AWS DataZone API Coverage**: Access all major DataZone operations
- **Modular Architecture**: Well-organized, maintainable code structure
- **Type Safety**: Full TypeScript-style type hints for Python
- **Comprehensive Error Handling**: Detailed error messages and proper exception handling
- **Production Ready**: Robust logging, validation, and configuration management

### 🛠️ Supported Operations

| Module | Operations |
|--------|------------|
| **Domain Management** | Create domains, manage domain units, search, policy grants |
| **Project Management** | Create/manage projects, project profiles, memberships |
| **Data Management** | Assets, listings, subscriptions, form types, data sources |
| **Glossary** | Business glossaries, glossary terms |
| **Environment** | Environments, connections, blueprints |

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- AWS credentials configured
- An active AWS DataZone domain

### Install from PyPI

```bash
pip install datazone-mcp-server
```

### Install from Source

```bash
git clone https://github.com/wangtianren/datazone-mcp-server.git
cd datazone-mcp-server
pip install -e .
```

## ⚡ Quick Start

### 1. Configure AWS Credentials

```bash
# Using AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### 2. Start the MCP Server

```bash
python -m datazone_mcp_server.server
```

### 3. Use with an MCP Client

```python
import asyncio
from mcp import create_client

async def main():
    # Connect to the DataZone MCP server
    client = await create_client("stdio", ["python", "-m", "datazone_mcp_server.server"])
    
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {len(tools.tools)}")
    
    # Call a DataZone operation
    result = await client.call_tool("get_domain", {
        "identifier": "dzd_your_domain_id"
    })
    print(result.content)

asyncio.run(main())
```

## 📚 Usage Examples

### Creating a DataZone Domain

```python
# Create a new DataZone domain
domain = await client.call_tool("create_domain", {
    "name": "MyDataDomain",
    "domain_execution_role": "arn:aws:iam::123456789012:role/DataZoneExecutionRole",
    "service_role": "arn:aws:iam::123456789012:role/DataZoneServiceRole",
    "description": "My data governance domain"
})
```

### Managing Projects

```python
# Create a project
project = await client.call_tool("create_project", {
    "domain_identifier": "dzd_abc123",
    "name": "Analytics Project",
    "description": "Project for analytics workloads"
})

# List projects
projects = await client.call_tool("list_projects", {
    "domain_identifier": "dzd_abc123"
})
```

### Working with Assets

```python
# Create an asset
asset = await client.call_tool("create_asset", {
    "domain_identifier": "dzd_abc123",
    "name": "Customer Data",
    "type_identifier": "amazon.datazone.RelationalTable",
    "owning_project_identifier": "prj_xyz789"
})

# Publish the asset
published = await client.call_tool("publish_asset", {
    "domain_identifier": "dzd_abc123",
    "asset_identifier": asset["id"]
})
```

## 🏗️ Architecture

```
datazone-mcp-server/
├── src/datazone_mcp_server/
│   ├── server.py              # Main MCP server entry point
│   ├── tools/                 # Tool modules
│   │   ├── common.py          # Shared utilities
│   │   ├── domain_management.py
│   │   ├── project_management.py
│   │   ├── data_management.py
│   │   ├── glossary.py
│   │   └── environment.py
│   └── __init__.py
├── tests/                     # Test suite
├── examples/                  # Usage examples
└── docs/                      # Documentation
```

## 🧪 Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/wangtianren/datazone-mcp-server.git
cd datazone-mcp-server

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=datazone_mcp_server

# Run specific test file
pytest tests/test_domain_management.py
```

### Code Quality

```bash
# Format code
black src tests
isort src tests

# Type checking
mypy src

# Linting
flake8 src tests
```

## 📋 Available Tools

<details>
<summary>Click to see all available MCP tools</summary>

### Domain Management
- `get_domain` - Retrieve domain information
- `create_domain` - Create a new domain
- `list_domain_units` - List domain units
- `create_domain_unit` - Create domain unit
- `add_entity_owner` - Add entity ownership
- `add_policy_grant` - Grant policies
- `search` - Search across DataZone

### Project Management
- `create_project` - Create new project
- `get_project` - Get project details
- `list_projects` - List all projects
- `create_project_membership` - Add project members
- `list_project_profiles` - List project profiles
- `create_project_profile` - Create project profile

### Data Management
- `get_asset` - Retrieve asset information
- `create_asset` - Create new asset
- `publish_asset` - Publish asset to catalog
- `get_listing` - Get asset listing
- `search_listings` - Search published assets
- `create_data_source` - Create data source
- `start_data_source_run` - Start data source run
- `create_subscription_request` - Request data subscription
- `accept_subscription_request` - Accept subscription
- `get_form_type` - Get metadata form type
- `create_form_type` - Create metadata form type

### Glossary Management
- `create_glossary` - Create business glossary
- `create_glossary_term` - Create glossary term
- `get_glossary` - Get glossary details
- `get_glossary_term` - Get term details

### Environment Management
- `list_environments` - List environments
- `create_connection` - Create environment connection
- `get_connection` - Get connection details
- `list_connections` - List all connections
- `list_environment_blueprints` - List available blueprints

</details>

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**This is an unofficial, community-developed project and is not affiliated with, endorsed by, or supported by Amazon Web Services, Inc.**

- AWS and DataZone are trademarks of Amazon.com, Inc. or its affiliates
- This project provides a community-built interface to AWS DataZone APIs
- Users are responsible for their own AWS credentials, costs, and compliance
- No warranty or support is provided - use at your own risk
- Always follow AWS security best practices when using this tool

For official AWS DataZone documentation and support, visit [AWS DataZone Documentation](https://docs.aws.amazon.com/datazone/).

## 🆘 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/wangtianren/datazone-mcp-server/issues)
- 💬 [Discussions](https://github.com/wangtianren/datazone-mcp-server/discussions)

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the protocol specification
- [AWS DataZone](https://aws.amazon.com/datazone/) for the data governance platform
- The open-source community for inspiration and contributions
