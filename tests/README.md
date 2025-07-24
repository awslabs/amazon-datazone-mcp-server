# Testing

Tests for the Amazon DataZone MCP Server using pytest.

## Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/amazon_datazone_mcp_server

# Run specific module tests
pytest tests/test_domain_management.py
```

## Test Structure

- `test_*_management.py` - Unit tests for each tool module (domain, project, data, etc.)
- `test_integration.py` - Integration tests with real AWS services
- `test_error_handling.py` - Error scenario testing
- `conftest.py` - Shared fixtures and mock helpers

## DataZone-Specific Testing

### Environment Variables (for integration tests)
```bash
export TEST_DATAZONE_DOMAIN_ID="dzd_your_domain_id"
export TEST_DATAZONE_PROJECT_ID="prj_your_project_id"
export AWS_DEFAULT_REGION="us-east-1"
```

### Mocking Pattern
```python
@patch('amazon_datazone_mcp_server.tools.domain_management.datazone_client')
async def test_function(self, mock_client):
    mock_client.operation.return_value = {"result": "data"}
    # Test logic here
```

### Integration Tests
```bash
# Run integration tests (requires AWS credentials)
pytest tests/test_integration.py -m integration

# Skip integration tests
pytest -m "not integration"
```

For detailed pytest usage, see the [pytest documentation](https://docs.pytest.org/).
