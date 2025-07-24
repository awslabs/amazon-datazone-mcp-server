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
   pip install -e .  # Install in development mode
   ```

4. **Install Development Dependencies**
   ```bash
   pip install -e ".[dev]"  # Install with dev dependencies
   ```

## Project Structure

```
amazon-datazone-mcp-server/
├── src/
│   └── amazon_datazone_mcp_server/    # Main package
│       ├── __init__.py
│       ├── server.py                  # MCP server entry point
│       └── tools/                     # DataZone tool implementations
│           ├── __init__.py
│           ├── common.py
│           ├── data_management.py
│           ├── domain_management.py
│           ├── environment.py
│           ├── glossary.py
│           └── project_management.py
├── tests/                             # Test suite (DataZone-only)
├── docs/                              # Documentation
├── pyproject.toml                     # Project configuration and dependencies
├── VERSION                            # Package version
└── README.md                          # User documentation
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/amazon_datazone_mcp_server --cov-report=html

# Run specific test file
pytest tests/test_datazone_mcp_server.py

# Run with verbose output
pytest -v

# Run only DataZone-specific tests
pytest tests/test_data_management.py tests/test_domain_management.py
```

## Code Quality

- **Formatting**: Use `black` for code formatting
- **Import sorting**: Use `isort` for import organization
- **Type hints**: Use type hints throughout the codebase
- **Linting**: Use `ruff` and `flake8` for code quality
- **Documentation**: Document all public functions and classes

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Run linting
ruff check src/ tests/
flake8 src/ tests/

# Type checking
mypy src/
```

## Running the Server

```bash
# Install the package
pip install -e .

# Run the DataZone MCP server
amazon-datazone-mcp-server

# Or run directly
python -m amazon_datazone_mcp_server.server
```

## Building for PyPI

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Check the built package
twine check dist/*

# Upload to PyPI (requires credentials)
twine upload dist/*
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite and ensure all tests pass
6. Submit a pull request

## AWS Configuration

The server requires AWS credentials to access DataZone APIs:

```bash
# Configure AWS CLI
aws configure

# Or use environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_SESSION_TOKEN=your_session_token  # If using temporary credentials
export AWS_DEFAULT_REGION=us-east-1
```

For local development, you can also set:
```bash
export MCP_LOCAL_DEV=true
```

## Release Process

1. Update `VERSION` file
2. Update `CHANGELOG.md` (if exists)
3. Create a git tag: `git tag v0.1.0`
4. Push tags: `git push --tags`
5. Build and upload to PyPI
