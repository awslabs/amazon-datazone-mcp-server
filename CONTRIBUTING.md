# Contributing to AWS DataZone MCP Server

Thank you for your interest in contributing to the AWS DataZone MCP Server! We welcome contributions from the community and are pleased to have you help make this project better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- AWS account with DataZone access
- Familiarity with the Model Context Protocol (MCP)

### Development Setup

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/awslabs/amazon-datazone-mcp-server.git
cd amazon-datazone-mcp-server
   ```

2. **Set Up Development Environment**
   ```bash
   # Create a virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install the package in development mode
   pip install -e ".[dev]"
   ```

3. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

4. **Configure AWS Credentials**
   ```bash
   aws configure
   # OR set environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

5. **Verify Setup**
   ```bash
   python -m pytest tests/
   python -c "import amazon_datazone_mcp_server; print('Setup successful!')"
   ```

## Making Changes

### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the coding standards
   - Add comprehensive tests
   - Update documentation

3. **Test your changes**
   ```bash
   pytest
   pytest --cov=src/amazon_datazone_mcp_server --cov-report=html
   black src tests
   isort src tests
   mypy src
   ```

### Tool Development

When adding new DataZone tools:

1. **Add the tool function** in the appropriate module (e.g., `src/amazon_datazone_mcp_server/tools/domain_management.py`)

2. **Register the tool** in the module's `register_tools()` function

3. **Add comprehensive tests**:
   ```python
   import pytest
   from unittest.mock import patch
   from amazon_datazone_mcp_server.tools import your_module

   class TestYourModule:
       @patch('amazon_datazone_mcp_server.tools.your_module.datazone_client')
   ```

### Error Handling Best Practices

- Always wrap DataZone API calls in try-catch blocks
- Handle specific AWS error codes when possible
- Provide meaningful error messages to users
- Log errors appropriately using the logger

### Documentation Requirements

- Add comprehensive docstrings to all functions
- Include parameter descriptions with types
- Provide usage examples in docstrings
- Update README.md if adding major features

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=datazone_mcp_server --cov-report=html

# Run specific test file
pytest tests/test_domain_management.py

# Run specific test
pytest tests/test_domain_management.py::test_create_domain
```

### Writing Tests

1. **Test File Structure**
   ```
   tests/
   ├── conftest.py              # Shared fixtures
   ├── test_domain_management.py
   ├── test_project_management.py
   ├── test_data_management.py
   ├── test_glossary.py
   └── test_environment.py
   ```

2. **Test Template**
   ```python
   import pytest
   from unittest.mock import Mock, patch
   from datazone_mcp_server.tools import your_module

   @pytest.fixture
   def mock_datazone_client():
       return Mock()

   @patch('datazone_mcp_server.tools.your_module.datazone_client')
   async def test_your_function(mock_client):
       # Arrange
       mock_client.your_api_method.return_value = {"result": "success"}
       # Act
       result = await your_module.your_function("param1", "param2")
       # Assert
       assert result["result"] == "success"
       mock_client.your_api_method.assert_called_once_with(
           param1="param1",
           param2="param2"
       )
   ```

### Test Coverage Requirements

- Aim for >80% code coverage
- Test both success and error scenarios
- Include edge cases and validation tests

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Type checking
mypy src

# Linting
flake8 src tests
```

### Style Configuration

The project uses:
- **Black** for code formatting (100 character line length)
- **isort** for import sorting
- **mypy** for type checking
- **flake8** for linting

### Type Hints

- Use type hints for all function parameters and return values
- Import types from `typing` module
- Use `Any` for complex AWS API responses
- Be consistent with `List`, `Dict`, etc. (not `list`, `dict`)

## Submitting Changes

### Pull Request Process

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write clean, well-documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   pytest
   black src tests
   isort src tests
   mypy src
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

### PR Requirements

- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] New functionality includes tests
- [ ] Documentation is updated
- [ ] No breaking changes (or clearly documented)
- [ ] PR description explains the change

### PR Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
```

## Reporting Issues

### Bug Reports

Use the issue template and include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)
- Error messages and stack traces

### Security Issues

For security vulnerabilities, please create a private security advisory on GitHub instead of creating a public issue.

## Feature Requests

We welcome feature requests! Please:
- Check existing issues first
- Provide clear use case description
- Explain why the feature would benefit users
- Consider implementation complexity

## Getting Help

- - Check the [documentation](docs/)
- - Join [discussions](https://github.com/awslabs/amazon-datazone-mcp-server/discussions)
- ## Browse [existing issues](https://github.com/awslabs/amazon-datazone-mcp-server/issues)
- 📧 Contact maintainers

## Recognition

Contributors will be recognized in:
- README.md acknowledgments
- CHANGELOG.md release notes
- GitHub contributors list

Thank you for contributing to Amazon DataZone MCP Server! ##
