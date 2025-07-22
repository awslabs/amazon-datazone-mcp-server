"""Tests for the Athena MCP server functionality."""

from unittest.mock import Mock, patch
import pytest
from botocore.exceptions import ClientError


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
        mock_sts_client.get_caller_identity.return_value = {
            "Account": "123456789012"
        }  # pragma: allowlist secret

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

        assert "Athena SQL query failed" in str(exc_info.value)

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
        mock_sts_client.get_caller_identity.return_value = {
            "Account": "123456789012"
        }  # pragma: allowlist secret

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
            # Use a function that returns increasing values to simulate timeout
            call_count = [0]

            def time_side_effect():
                call_count[0] += 1
                if call_count[0] == 1:
                    return 0  # start_time
                else:
                    return 400  # All subsequent calls return a time that exceeds max_wait_time (300)

            mock_time.side_effect = time_side_effect

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

        assert "Athena SQL query failed" in str(exc_info.value)

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

        assert "Athena SQL query failed" in str(exc_info.value)


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
        mock_sts_client.get_caller_identity.return_value = {
            "Account": "123456789012"
        }  # pragma: allowlist secret

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
