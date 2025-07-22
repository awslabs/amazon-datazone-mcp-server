# Development Guide

This document provides guidance for developers who want to contribute to or modify the Amazon DataZone MCP Server.

## Development Environment Setup

### Prerequisites

- Python 3.10 or higher
- Git
- AWS CLI configured with appropriate credentials
- Virtual environment tool (venv, conda, etc.)

### Local Development Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/awslabs/amazon-datazone-mcp-server.git
   cd amazon-datazone-mcp-server
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

4. **Install Development Dependencies**
   ```bash
   pip install pytest pytest-cov pytest-asyncio black isort mypy
   ```

## Project Structure

```
amazon-datazone-mcp-server/
├── servers/                    # MCP server implementations
│   ├── datazone/              # Main DataZone MCP server
│   ├── athena/                # Athena-specific server
│   ├── glue/                  # Glue-specific server
│   ├── s3/                    # S3-specific server
│   └── shared/                # Shared utilities
├── tests/                     # Test suite
├── docs/                      # Documentation
├── requirements.txt           # Dependencies
├── pyproject.toml            # Project configuration
└── README.md                 # Main documentation
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=servers --cov-report=html

# Run specific test file
pytest tests/test_datazone_mcp_server.py

# Run with verbose output
pytest -v
```


- **Formatting**: Use `black` for code formatting
- **Import sorting**: Use `isort` for import organization
- **Type hints**: Use type hints throughout the codebase
- **Documentation**: Document all public functions and classes

```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy servers/
```

## Running the Servers

All servers use stdio transport for secure communication:

```bash
# DataZone MCP Server
python servers/datazone/server.py

# Individual service servers
python servers/athena/server.py
python servers/glue/server.py
python servers/s3/server.py
```

## AWS Configuration

Ensure your AWS credentials are properly configured:

```bash
# Via AWS CLI
aws configure

# Or via environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Debugging

Use Python's built-in logging for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Architecture Notes

- **MCP Protocol**: All servers implement the Model Context Protocol specification
- **AWS SDK**: Uses boto3 for AWS API interactions
- **Error Handling**: Comprehensive error handling with proper JSON-RPC responses
- **Type Safety**: Full type annotations for better development experience
