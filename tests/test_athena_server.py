"""Tests for the Athena MCP server functionality."""

import json
import os
from unittest.mock import Mock, patch
import pytest
from botocore.exceptions import ClientError


class TestGetMCPCredentials:
    """Test get_mcp_credentials function."""

    @patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "ASIAQGYBP5OXW5MTKVKQ123456",  # pragma: allowlist secret
            "AWS_SECRET_ACCESS_KEY": "test-secret",
            "AWS_SESSION_TOKEN": "test-token",
            "AWS_DEFAULT_REGION": "us-west-2",
        },
    )
    def test_local_development_credentials(self):
        """Test credentials from environment variables for local development."""
        from servers.athena.server import get_mcp_credentials

        result = get_mcp_credentials()

        assert result is not None
        assert (
            result["aws_access_key_id"] == "ASIAQGYBP5OXW5MTKVKQ123456"
        )  # pragma: allowlist secret
        assert result["aws_secret_access_key"] == "test-secret"
        assert result["aws_session_token"] == "test-token"
        assert result["region_name"] == "us-west-2"
        assert result["account_id"] == "014498655151"

    @patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",  # Different pattern  # pragma: allowlist secret
            "AWS_SECRET_ACCESS_KEY": "test-secret",
            "AWS_SESSION_TOKEN": "test-token",
        },
    )
    @patch("boto3.client")
    def test_secrets_manager_retrieval(self, mock_boto_client):
        """Test credentials retrieval from Secrets Manager."""
        from servers.athena.server import get_mcp_credentials

        # Mock secrets manager response
        mock_secrets_client = Mock()
        mock_boto_client.return_value = mock_secrets_client
        mock_secrets_client.get_secret_value.return_value = {
            "SecretString": json.dumps(
                {
                    "AWS_ACCESS_KEY_ID": "secrets-access-key",
                    "AWS_SECRET_ACCESS_KEY": "secrets-secret-key",
                    "AWS_SESSION_TOKEN": "secrets-session-token",
                    "AWS_DEFAULT_REGION": "us-east-1",
                    "ACCOUNT_ID": "123456789012",
                }
            )
        }

        result = get_mcp_credentials()

        assert result is not None
        assert result["aws_access_key_id"] == "secrets-access-key"
        assert result["aws_secret_access_key"] == "secrets-secret-key"
        assert result["aws_session_token"] == "secrets-session-token"
        assert result["region_name"] == "us-east-1"
        assert result["account_id"] == "123456789012"

        # Verify secrets manager was called correctly
        mock_boto_client.assert_called_with("secretsmanager", region_name="us-east-1")
        mock_secrets_client.get_secret_value.assert_called_with(
            SecretId="smus-ai/dev/mcp-aws-credentials"
        )  # pragma: allowlist secret

    @patch.dict(os.environ, {}, clear=True)
    @patch("boto3.client")
    def test_secrets_manager_failure_fallback(self, mock_boto_client):
        """Test fallback to None when Secrets Manager fails."""
        from servers.athena.server import get_mcp_credentials

        # Mock secrets manager to raise an exception
        mock_secrets_client = Mock()
        mock_boto_client.return_value = mock_secrets_client
        mock_secrets_client.get_secret_value.side_effect = Exception("Access denied")

        result = get_mcp_credentials()

        assert result is None


class TestAthenaExecuteSQLQuery:
    """Test athena_execute_sql_query tool."""

    @patch("servers.athena.server.datazone_client")
    @patch("servers.athena.server.sts_client")
    @patch("servers.athena.server.athena_client")
    @patch("servers.athena.server.s3_client")
    @patch("boto3.session.Session")
    async def test_execute_sql_query_success(
        self,
        mock_session,
        mock_s3_client,
        mock_athena_client,
        mock_sts_client,
        mock_datazone_client,
    ):
        """Test successful SQL query execution."""
        from servers.athena.server import athena_execute_sql_query

        # Mock session region
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.region_name = "us-east-1"

        # Mock STS get_caller_identity
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        # Mock DataZone list_environments
        mock_datazone_client.list_environments.return_value = {
            "items": [{"status": "ACTIVE", "environmentId": "env-123"}]
        }

        # Mock DataZone list_connections
        mock_datazone_client.list_connections.return_value = {
            "items": [
                {
                    "type": "ATHENA",
                    "props": {"athenaProperties": {"workgroupName": "primary"}},
                }
            ]
        }

        # Mock Athena start_query_execution response
        mock_athena_client.start_query_execution.return_value = {
            "QueryExecutionId": "query-123"
        }

        # Mock Athena get_query_execution responses
        mock_athena_client.get_query_execution.side_effect = [
            {
                "QueryExecution": {
                    "QueryExecutionId": "query-123",
                    "Status": {"State": "RUNNING"},
                }
            },
            {
                "QueryExecution": {
                    "QueryExecutionId": "query-123",
                    "Status": {"State": "SUCCEEDED"},
                    "ResultConfiguration": {
                        "OutputLocation": "s3://bucket/query-results/"
                    },
                    "Statistics": {
                        "TotalExecutionTimeInMillis": 1000,
                        "DataScannedInBytes": 2048,
                    },
                }
            },
        ]

        # Mock Athena get_query_results
        mock_athena_client.get_query_results.return_value = {
            "ResultSet": {
                "ResultSetMetadata": {
                    "ColumnInfo": [
                        {"Name": "col1", "Type": "varchar"},
                        {"Name": "col2", "Type": "bigint"},
                    ]
                },
                "Rows": [
                    {"Data": [{"VarCharValue": "col1"}, {"VarCharValue": "col2"}]},
                    {"Data": [{"VarCharValue": "value1"}, {"VarCharValue": "123"}]},
                ],
            }
        }

        result = await athena_execute_sql_query(
            domain_identifier="dzd_test123",
            project_identifier="prj_test123",
            sql_query="SELECT * FROM test_table LIMIT 10",
            database_name="test_db",
            max_results=100,
        )

        assert result is not None
        assert "columns" in result
        assert "rows" in result
        assert len(result["columns"]) == 2
        assert len(result["rows"]) == 1
        assert result["columns"][0]["name"] == "col1"
        assert result["rows"][0] == ["value1", "123"]

        # Verify client calls
        mock_datazone_client.list_environments.assert_called_once()
        mock_datazone_client.list_connections.assert_called_once()
        mock_athena_client.start_query_execution.assert_called_once()

    @patch("servers.athena.server.datazone_client")
    @patch("servers.athena.server.athena_client")
    async def test_execute_sql_query_failed(
        self, mock_athena_client, mock_datazone_client
    ):
        """Test SQL query execution failure."""
        from servers.athena.server import athena_execute_sql_query

        # Mock DataZone to fail
        mock_datazone_client.list_environments.side_effect = ClientError(
            {
                "Error": {
                    "Code": "UnrecognizedClientException",
                    "Message": "Invalid token",
                }
            },
            "ListEnvironments",
        )

        with pytest.raises(Exception) as exc_info:
            await athena_execute_sql_query(
                domain_identifier="dzd_test123",
                project_identifier="prj_test123",
                sql_query="SELECT * FROM test_table",
                database_name="test_db",
            )

        assert "Error executing SQL query" in str(exc_info.value)

    @patch("servers.athena.server.datazone_client")
    @patch("servers.athena.server.sts_client")
    @patch("servers.athena.server.athena_client")
    @patch("boto3.session.Session")
    @patch("time.sleep")  # Mock sleep to speed up test
    async def test_execute_sql_query_timeout(
        self,
        mock_sleep,
        mock_session,
        mock_athena_client,
        mock_sts_client,
        mock_datazone_client,
    ):
        """Test SQL query execution timeout."""
        from servers.athena.server import athena_execute_sql_query

        # Mock session region
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.region_name = "us-east-1"

        # Mock STS get_caller_identity
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        # Mock DataZone list_environments
        mock_datazone_client.list_environments.return_value = {
            "items": [{"status": "ACTIVE", "environmentId": "env-123"}]
        }

        # Mock DataZone list_connections
        mock_datazone_client.list_connections.return_value = {
            "items": [
                {
                    "type": "ATHENA",
                    "props": {"athenaProperties": {"workgroupName": "primary"}},
                }
            ]
        }

        # Mock Athena start_query_execution response
        mock_athena_client.start_query_execution.return_value = {
            "QueryExecutionId": "query-123"
        }

        # Mock Athena get_query_execution to always return RUNNING
        mock_athena_client.get_query_execution.return_value = {
            "QueryExecution": {
                "QueryExecutionId": "query-123",
                "Status": {"State": "RUNNING"},
            }
        }

        # Mock time.time to simulate timeout
        with patch("time.time") as mock_time:
            # First call returns 0, subsequent calls return large values to trigger timeout
            mock_time.side_effect = [0, 0, 400]  # 400 > 300 (max_wait_time)

            with pytest.raises(Exception) as exc_info:
                await athena_execute_sql_query(
                    domain_identifier="dzd_test123",
                    project_identifier="prj_test123",
                    sql_query="SELECT * FROM test_table",
                    database_name="test_db",
                )

            assert "timed out" in str(exc_info.value).lower()


class TestAthenaDescribeAvailableTables:
    """Test athena_describe_available_tables tool."""

    @patch("servers.athena.server.athena_client")
    async def test_describe_available_tables_success(self, mock_athena_client):
        """Test successful table description."""
        from servers.athena.server import athena_describe_available_tables

        # Mock Athena list_table_metadata response
        mock_athena_client.list_table_metadata.return_value = {
            "TableMetadataList": [
                {
                    "Name": "test_table1",
                    "TableType": "EXTERNAL_TABLE",
                    "CreateTime": "2023-01-01T00:00:00Z",
                    "LastAccessTime": "2023-01-02T00:00:00Z",
                    "Parameters": {"key": "value"},
                    "Columns": [
                        {"Name": "col1", "Type": "string", "Comment": "First column"},
                        {"Name": "col2", "Type": "bigint", "Comment": "Second column"},
                    ],
                },
                {
                    "Name": "test_table2",
                    "TableType": "MANAGED_TABLE",
                    "Columns": [{"Name": "col3", "Type": "double"}],
                },
            ],
            "NextToken": "next-token-123",
        }

        result = await athena_describe_available_tables(
            database_name="test_db",
            workgroup="primary",
            catalog_name="AwsDataCatalog",
            max_results=50,
        )

        assert result is not None
        assert "tables" in result
        assert len(result["tables"]) == 2
        assert result["tables"][0]["name"] == "test_table1"
        assert result["tables"][1]["name"] == "test_table2"
        assert "next_token" in result
        assert result["next_token"] == "next-token-123"

        # Verify Athena client call - note the correct parameter order
        mock_athena_client.list_table_metadata.assert_called_once_with(
            DatabaseName="test_db",
            MaxResults=50,
            WorkGroup="primary",
            CatalogName="AwsDataCatalog",
        )

    @patch("servers.athena.server.athena_client")
    async def test_describe_available_tables_with_next_token(self, mock_athena_client):
        """Test table description with next token."""
        from servers.athena.server import athena_describe_available_tables

        # Mock Athena list_table_metadata response
        mock_athena_client.list_table_metadata.return_value = {
            "TableMetadataList": [
                {
                    "Name": "test_table3",
                    "TableType": "EXTERNAL_TABLE",
                    "Columns": [{"Name": "col1", "Type": "string"}],
                }
            ]
        }

        result = await athena_describe_available_tables(
            database_name="test_db", next_token="prev-token-123"
        )

        assert result is not None
        assert "tables" in result
        assert len(result["tables"]) == 1
        assert result["tables"][0]["name"] == "test_table3"

        # Verify Athena client call with next token - note MaxResults is always added
        mock_athena_client.list_table_metadata.assert_called_once_with(
            DatabaseName="test_db", MaxResults=50, NextToken="prev-token-123"
        )

    @patch("servers.athena.server.athena_client")
    async def test_describe_available_tables_error(self, mock_athena_client):
        """Test table description error handling."""
        from servers.athena.server import athena_describe_available_tables

        # Mock Athena list_table_metadata to raise an error
        mock_athena_client.list_table_metadata.side_effect = ClientError(
            {
                "Error": {
                    "Code": "EntityNotFoundException",
                    "Message": "Database not found",
                }
            },
            "ListTableMetadata",
        )

        with pytest.raises(Exception) as exc_info:
            await athena_describe_available_tables(database_name="nonexistent_db")

        assert "Error describing tables" in str(exc_info.value)


class TestCreateHTTPApp:
    """Test create_http_app function."""

    @patch("servers.athena.server.mcp")
    def test_create_http_app_success(self, mock_mcp):
        """Test successful HTTP app creation."""
        try:
            from servers.athena.server import create_http_app

            app = create_http_app()
            if app is None:
                pytest.skip("FastAPI not available - skipping HTTP app test")
            else:
                assert app is not None
        except Exception as e:
            if "fastapi" in str(e).lower():
                pytest.skip("FastAPI not installed - skipping HTTP app tests")
            else:
                raise

    def test_health_endpoint(self):
        """Test health endpoint."""
        try:
            from fastapi.testclient import TestClient
            from servers.athena.server import create_http_app

            with patch("servers.athena.server.mcp") as mock_mcp:
                mock_mcp._tool_manager._tools = {}
                app = create_http_app()
                if app is None:
                    pytest.skip("FastAPI not available - skipping health endpoint test")
                else:
                    client = TestClient(app)

                    response = client.get("/health")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "healthy"
                    assert data["service"] == "athena-mcp-server"
        except ImportError:
            pytest.skip("FastAPI not installed - skipping HTTP endpoint tests")

    def test_root_endpoint(self):
        """Test root endpoint."""
        try:
            from fastapi.testclient import TestClient
            from servers.athena.server import create_http_app

            with patch("servers.athena.server.mcp") as mock_mcp:
                mock_mcp._tool_manager._tools = {}
                app = create_http_app()
                if app is None:
                    pytest.skip("FastAPI not available - skipping root endpoint test")
                else:
                    client = TestClient(app)

                    response = client.get("/")

                    assert response.status_code == 200
                    data = response.json()
                    assert "service" in data
        except ImportError:
            pytest.skip("FastAPI not installed - skipping HTTP endpoint tests")

    def test_mcp_endpoint(self):
        """Test MCP endpoint."""
        try:
            from fastapi.testclient import TestClient
            from servers.athena.server import create_http_app

            with patch("servers.athena.server.mcp") as mock_mcp:
                mock_mcp._tool_manager._tools = {}
                app = create_http_app()
                if app is None:
                    pytest.skip("FastAPI not available - skipping MCP endpoint test")
                else:
                    client = TestClient(app)

                    response = client.get("/mcp/athena")

                    assert response.status_code == 200
                    data = response.json()
                    assert "result" in data
        except ImportError:
            pytest.skip("FastAPI not installed - skipping HTTP endpoint tests")


class TestModuleImports:
    """Test module imports and initialization."""

    def test_server_module_imports(self):
        """Test that the server module can be imported successfully."""
        try:
            import servers.athena.server

            assert servers.athena.server is not None
        except ImportError as e:
            pytest.fail(f"Failed to import athena server module: {e}")

    def test_required_dependencies(self):
        """Test that required dependencies are available."""
        try:
            import boto3
            import mcp.server.fastmcp

            assert boto3 is not None
            assert mcp.server.fastmcp is not None
        except ImportError as e:
            pytest.fail(f"Missing required dependency: {e}")


class TestEnvironmentConfiguration:
    """Test environment configuration handling."""

    def test_default_region(self):
        """Test default region configuration."""
        from servers.athena.server import get_mcp_credentials

        with patch.dict(
            os.environ,
            {
                "AWS_ACCESS_KEY_ID": "ASIAQGYBP5OXW5MTKVKQ123456",  # pragma: allowlist secret
                "AWS_SECRET_ACCESS_KEY": "test-secret",
                "AWS_SESSION_TOKEN": "test-token",
                # No AWS_DEFAULT_REGION
            },
        ):
            result = get_mcp_credentials()
            assert result is not None
            assert result["region_name"] == "us-east-1"  # Default region

    def test_custom_region(self):
        """Test custom region configuration."""
        from servers.athena.server import get_mcp_credentials

        with patch.dict(
            os.environ,
            {
                "AWS_ACCESS_KEY_ID": "ASIAQGYBP5OXW5MTKVKQ123456",  # pragma: allowlist secret
                "AWS_SECRET_ACCESS_KEY": "test-secret",
                "AWS_SESSION_TOKEN": "test-token",
                "AWS_DEFAULT_REGION": "us-west-2",
            },
        ):
            result = get_mcp_credentials()
            assert result is not None
            assert result["region_name"] == "us-west-2"


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch("servers.athena.server.datazone_client")
    async def test_client_not_initialized(self, mock_datazone_client):
        """Test behavior when AWS client encounters authentication issues."""
        from servers.athena.server import athena_execute_sql_query

        # Mock DataZone to raise authentication error
        mock_datazone_client.list_environments.side_effect = ClientError(
            {
                "Error": {
                    "Code": "UnrecognizedClientException",
                    "Message": "Invalid token",
                }
            },
            "ListEnvironments",
        )

        with pytest.raises(Exception) as exc_info:
            await athena_execute_sql_query(
                domain_identifier="dzd_test123",
                project_identifier="prj_test123",
                sql_query="SELECT * FROM test_table",
                database_name="test_db",
            )

        assert "Error executing SQL query" in str(exc_info.value)

    @patch("servers.athena.server.datazone_client")
    async def test_invalid_parameters(self, mock_datazone_client):
        """Test handling of invalid parameters."""
        from servers.athena.server import athena_execute_sql_query

        # Mock DataZone to raise validation error
        mock_datazone_client.list_environments.side_effect = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid parameter"}},
            "ListEnvironments",
        )

        with pytest.raises(Exception) as exc_info:
            await athena_execute_sql_query(
                domain_identifier="invalid",
                project_identifier="prj_test123",
                sql_query="SELECT * FROM test_table",
                database_name="test_db",
            )

        assert "Error executing SQL query" in str(exc_info.value)


class TestIntegration:
    """Test integration scenarios."""

    @patch("servers.athena.server.datazone_client")
    @patch("servers.athena.server.sts_client")
    @patch("servers.athena.server.athena_client")
    @patch("servers.athena.server.s3_client")
    @patch("boto3.session.Session")
    async def test_full_query_workflow(
        self,
        mock_session,
        mock_s3_client,
        mock_athena_client,
        mock_sts_client,
        mock_datazone_client,
    ):
        """Test complete query workflow."""
        from servers.athena.server import athena_execute_sql_query

        # Mock session region
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.region_name = "us-east-1"

        # Mock STS get_caller_identity
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        # Mock DataZone responses
        mock_datazone_client.list_environments.return_value = {
            "items": [{"status": "ACTIVE", "environmentId": "env-123"}]
        }

        mock_datazone_client.list_connections.return_value = {
            "items": [
                {
                    "type": "ATHENA",
                    "props": {"athenaProperties": {"workgroupName": "primary"}},
                }
            ]
        }

        # Mock Athena responses
        mock_athena_client.start_query_execution.return_value = {
            "QueryExecutionId": "query-456"
        }

        mock_athena_client.get_query_execution.return_value = {
            "QueryExecution": {
                "QueryExecutionId": "query-456",
                "Status": {"State": "SUCCEEDED"},
                "Statistics": {
                    "TotalExecutionTimeInMillis": 2000,
                    "DataScannedInBytes": 4096,
                },
            }
        }

        mock_athena_client.get_query_results.return_value = {
            "ResultSet": {
                "ResultSetMetadata": {
                    "ColumnInfo": [
                        {"Name": "id", "Type": "bigint"},
                        {"Name": "name", "Type": "varchar"},
                    ]
                },
                "Rows": [
                    {"Data": [{"VarCharValue": "id"}, {"VarCharValue": "name"}]},
                    {"Data": [{"VarCharValue": "1"}, {"VarCharValue": "test"}]},
                ],
            }
        }

        result = await athena_execute_sql_query(
            domain_identifier="dzd_test123",
            project_identifier="prj_test123",
            sql_query="SELECT id, name FROM users LIMIT 1",
            database_name="test_db",
        )

        assert result is not None
        assert "columns" in result
        assert "rows" in result
        assert len(result["columns"]) == 2
        assert len(result["rows"]) == 1
        assert result["execution_time_ms"] == 2000
        assert result["data_scanned_bytes"] == 4096
