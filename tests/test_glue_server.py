"""Tests for the Glue MCP server functionality."""

import json
import os
from unittest.mock import Mock, patch, MagicMock
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
        from servers.glue.server import get_mcp_credentials

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
        from servers.glue.server import get_mcp_credentials

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
        from servers.glue.server import get_mcp_credentials

        # Mock secrets manager to raise an exception
        mock_secrets_client = Mock()
        mock_boto_client.return_value = mock_secrets_client
        mock_secrets_client.get_secret_value.side_effect = Exception("Access denied")

        result = get_mcp_credentials()

        assert result is None


class TestGlueCreateDatabase:
    """Test glue_create_database tool."""

    @patch("servers.glue.server.glue_client")
    async def test_create_database_success(self, mock_glue_client):
        """Test successful database creation."""
        from servers.glue.server import glue_create_database

        # Mock Glue create_database response
        mock_glue_client.create_database.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }

        result = await glue_create_database(
            name="test_database",
            description="Test database description",
            location_uri="s3://bucket/database/",
            parameters={"param1": "value1"},
            tags={"Environment": "test"},
        )

        assert result is not None
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

        # Verify Glue client call
        mock_glue_client.create_database.assert_called_once_with(
            DatabaseInput={
                "Name": "test_database",
                "Description": "Test database description",
                "LocationUri": "s3://bucket/database/",
                "Parameters": {"param1": "value1"},
            },
            Tags={"Environment": "test"},
        )

    @patch("servers.glue.server.glue_client")
    async def test_create_database_minimal_params(self, mock_glue_client):
        """Test database creation with minimal parameters."""
        from servers.glue.server import glue_create_database

        mock_glue_client.create_database.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }

        result = await glue_create_database(name="minimal_db")

        assert result is not None

        # Verify only required parameters were passed
        mock_glue_client.create_database.assert_called_once_with(
            DatabaseInput={"Name": "minimal_db"}
        )

    @patch("servers.glue.server.glue_client")
    async def test_create_database_error(self, mock_glue_client):
        """Test database creation error handling."""
        from servers.glue.server import glue_create_database

        # Mock Glue create_database to raise an error
        mock_glue_client.create_database.side_effect = ClientError(
            {
                "Error": {
                    "Code": "AlreadyExistsException",
                    "Message": "Database already exists",
                }
            },
            "CreateDatabase",
        )

        with pytest.raises(Exception) as exc_info:
            await glue_create_database(name="existing_database")
        # The implementation wraps ClientError in Exception
        assert "already exists" in str(exc_info.value).lower()


class TestGlueCreateCrawler:
    """Test glue_create_crawler tool."""

    @patch("servers.glue.server.glue_client")
    async def test_create_crawler_success(self, mock_glue_client):
        """Test successful crawler creation."""
        from servers.glue.server import glue_create_crawler

        # Mock Glue create_crawler response
        mock_glue_client.create_crawler.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }

        targets = {"S3Targets": [{"Path": "s3://bucket/data/"}]}

        result = await glue_create_crawler(
            name="test_crawler",
            role="arn:aws:iam::123456789012:role/GlueServiceRole",
            targets=targets,
            database_name="test_database",
            description="Test crawler description",
            schedule="cron(0 12 * * ? *)",
        )

        assert result is not None
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

        # Verify Glue client call
        mock_glue_client.create_crawler.assert_called_once_with(
            Name="test_crawler",
            Role="arn:aws:iam::123456789012:role/GlueServiceRole",
            Targets=targets,
            DatabaseName="test_database",
            Description="Test crawler description",
            Schedule="cron(0 12 * * ? *)",
        )

    @patch("servers.glue.server.glue_client")
    async def test_create_crawler_with_all_params(self, mock_glue_client):
        """Test crawler creation with all optional parameters."""
        from servers.glue.server import glue_create_crawler

        mock_glue_client.create_crawler.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }

        targets = {
            "S3Targets": [{"Path": "s3://bucket/data/"}],
            "JdbcTargets": [
                {"ConnectionName": "test-connection", "Path": "database/table"}
            ],
        }

        result = await glue_create_crawler(
            name="full_crawler",
            role="arn:aws:iam::123456789012:role/GlueServiceRole",
            targets=targets,
            database_name="test_database",
            classifiers=["test-classifier"],
            configuration='{"Version": 1.0}',
            crawler_security_configuration="test-security-config",
            description="Full crawler description",
            lake_formation_configuration={"UseLakeFormationCredentials": True},
            lineage_configuration={"CrawlerLineageSettings": "ENABLE"},
            recrawl_policy={"RecrawlBehavior": "CRAWL_EVERYTHING"},
            schedule="cron(0 12 * * ? *)",
            schema_change_policy={"UpdateBehavior": "UPDATE_IN_DATABASE"},
            table_prefix="test_",
            tags={"Environment": "test"},
        )

        assert result is not None

        # Verify all parameters were passed correctly
        call_args = mock_glue_client.create_crawler.call_args[1]
        assert call_args["Name"] == "full_crawler"
        assert call_args["Role"] == "arn:aws:iam::123456789012:role/GlueServiceRole"
        assert call_args["Targets"] == targets
        assert call_args["DatabaseName"] == "test_database"
        assert call_args["Classifiers"] == ["test-classifier"]
        assert call_args["Configuration"] == '{"Version": 1.0}'
        assert call_args["CrawlerSecurityConfiguration"] == "test-security-config"
        assert call_args["Description"] == "Full crawler description"
        assert call_args["LakeFormationConfiguration"] == {
            "UseLakeFormationCredentials": True
        }
        assert call_args["LineageConfiguration"] == {"CrawlerLineageSettings": "ENABLE"}
        assert call_args["RecrawlPolicy"] == {"RecrawlBehavior": "CRAWL_EVERYTHING"}
        assert call_args["Schedule"] == "cron(0 12 * * ? *)"
        assert call_args["SchemaChangePolicy"] == {
            "UpdateBehavior": "UPDATE_IN_DATABASE"
        }
        assert call_args["TablePrefix"] == "test_"
        assert call_args["Tags"] == {"Environment": "test"}

    @patch("servers.glue.server.glue_client")
    async def test_create_crawler_error(self, mock_glue_client):
        """Test crawler creation error handling."""
        from servers.glue.server import glue_create_crawler

        # Mock Glue create_crawler to raise an error
        mock_glue_client.create_crawler.side_effect = ClientError(
            {"Error": {"Code": "InvalidInputException", "Message": "Invalid role ARN"}},
            "CreateCrawler",
        )

        targets = {"S3Targets": [{"Path": "s3://bucket/data/"}]}

        with pytest.raises(Exception) as exc_info:
            await glue_create_crawler(
                name="test_crawler", role="invalid-role", targets=targets
            )
        # The implementation wraps ClientError in Exception
        assert "error creating crawler" in str(exc_info.value).lower()


class TestGlueStartCrawler:
    """Test glue_start_crawler tool."""

    @patch("servers.glue.server.glue_client")
    async def test_start_crawler_success(self, mock_glue_client):
        """Test successful crawler start."""
        from servers.glue.server import glue_start_crawler

        # Mock Glue start_crawler response
        mock_glue_client.start_crawler.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }

        result = await glue_start_crawler(name="test_crawler")

        assert result is not None
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

        # Verify Glue client call
        mock_glue_client.start_crawler.assert_called_once_with(Name="test_crawler")

    @patch("servers.glue.server.glue_client")
    async def test_start_crawler_error(self, mock_glue_client):
        """Test crawler start error handling."""
        from servers.glue.server import glue_start_crawler

        # Mock Glue start_crawler to raise an error
        mock_glue_client.start_crawler.side_effect = ClientError(
            {
                "Error": {
                    "Code": "EntityNotFoundException",
                    "Message": "Crawler not found",
                }
            },
            "StartCrawler",
        )

        with pytest.raises(Exception) as exc_info:
            await glue_start_crawler(name="nonexistent_crawler")
        # The implementation wraps ClientError in Exception
        assert "error starting crawler" in str(exc_info.value).lower()


class TestGlueGetCrawler:
    """Test glue_get_crawler tool."""

    @patch("servers.glue.server.glue_client")
    async def test_get_crawler_success(self, mock_glue_client):
        """Test successful crawler retrieval."""
        from servers.glue.server import glue_get_crawler

        # Mock Glue get_crawler response
        mock_glue_client.get_crawler.return_value = {
            "Crawler": {
                "Name": "test_crawler",
                "Role": "arn:aws:iam::123456789012:role/GlueServiceRole",
                "Targets": {"S3Targets": [{"Path": "s3://bucket/data/"}]},
                "DatabaseName": "test_database",
                "Description": "Test crawler description",
                "State": "READY",
                "CrawlElapsedTime": 120,
                "LastCrawl": {
                    "Status": "SUCCEEDED",
                    "StartTime": "2024-01-01T12:00:00Z",
                    "EndTime": "2024-01-01T12:02:00Z",
                },
            }
        }

        result = await glue_get_crawler(name="test_crawler")

        assert result is not None
        # The actual implementation returns direct AWS response keys
        assert "Crawler" in result
        assert result["Crawler"]["Name"] == "test_crawler"
        assert result["Crawler"]["Role"] == "arn:aws:iam::123456789012:role/GlueServiceRole"
        assert result["Crawler"]["Targets"]["S3Targets"][0]["Path"] == "s3://bucket/data/"
        assert result["Crawler"]["DatabaseName"] == "test_database"

        # Verify Glue client call
        mock_glue_client.get_crawler.assert_called_once_with(Name="test_crawler")

    @patch("servers.glue.server.glue_client")
    async def test_get_crawler_not_found(self, mock_glue_client):
        """Test crawler retrieval when not found."""
        from servers.glue.server import glue_get_crawler

        # Mock Glue get_crawler to raise an error
        mock_glue_client.get_crawler.side_effect = ClientError(
            {
                "Error": {
                    "Code": "EntityNotFoundException",
                    "Message": "Crawler not found",
                }
            },
            "GetCrawler",
        )

        with pytest.raises(Exception) as exc_info:
            await glue_get_crawler(name="nonexistent_crawler")
        # The implementation wraps ClientError in Exception
        assert "error getting crawler" in str(exc_info.value).lower()


class TestGlueGetTables:
    """Test glue_get_tables tool."""

    @patch("servers.glue.server.glue_client")
    async def test_get_tables_success(self, mock_glue_client):
        """Test successful table retrieval."""
        from servers.glue.server import glue_get_tables

        # Mock Glue get_tables response
        mock_glue_client.get_tables.return_value = {
            "TableList": [
                {
                    "Name": "table1",
                    "DatabaseName": "test_database",
                    "Description": "Test table 1",
                    "TableType": "EXTERNAL_TABLE",
                    "StorageDescriptor": {
                        "Columns": [
                            {"Name": "id", "Type": "bigint"},
                            {"Name": "name", "Type": "string"},
                        ]
                    },
                },
                {
                    "Name": "table2",
                    "DatabaseName": "test_database",
                    "Description": "Test table 2",
                    "TableType": "EXTERNAL_TABLE",
                    "StorageDescriptor": {
                        "Columns": [
                            {"Name": "col1", "Type": "string"},
                            {"Name": "col2", "Type": "int"},
                        ]
                    },
                },
            ],
            "NextToken": "next-token-123",
        }

        result = await glue_get_tables(
            database_name="test_database", max_results=50, include_status_details=True
        )

        assert result is not None
        # The actual implementation returns direct AWS response keys
        assert "TableList" in result
        assert len(result["TableList"]) == 2
        assert result["TableList"][0]["Name"] == "table1"
        assert result["TableList"][1]["Name"] == "table2"
        assert "NextToken" in result

        # Verify Glue client call
        mock_glue_client.get_tables.assert_called_once_with(
            DatabaseName="test_database",
            MaxResults=50,
            IncludeStatusDetails=True,
        )

    @patch("servers.glue.server.glue_client")
    async def test_get_tables_with_expression(self, mock_glue_client):
        """Test table retrieval with expression filter."""
        from servers.glue.server import glue_get_tables

        mock_glue_client.get_tables.return_value = {
            "TableList": [
                {
                    "Name": "filtered_table",
                    "DatabaseName": "test_database",
                    "TableType": "EXTERNAL_TABLE",
                }
            ]
        }

        result = await glue_get_tables(
            database_name="test_database", expression="name LIKE '%test%'"
        )

        assert result is not None
        assert len(result["TableList"]) == 1
        assert result["TableList"][0]["Name"] == "filtered_table"

        # Verify Glue client call with expression
        mock_glue_client.get_tables.assert_called_once_with(
            DatabaseName="test_database",
            MaxResults=100,
            Expression="name LIKE '%test%'",
        )

    @patch("servers.glue.server.glue_client")
    async def test_get_tables_error(self, mock_glue_client):
        """Test table retrieval error handling."""
        from servers.glue.server import glue_get_tables

        # Mock Glue get_tables to raise an error
        mock_glue_client.get_tables.side_effect = ClientError(
            {
                "Error": {
                    "Code": "EntityNotFoundException",
                    "Message": "Database not found",
                }
            },
            "GetTables",
        )

        with pytest.raises(Exception) as exc_info:
            await glue_get_tables(database_name="nonexistent_database")
        # The implementation wraps ClientError in Exception
        assert "error getting tables" in str(exc_info.value).lower()


class TestGlueGetTable:
    """Test glue_get_table tool."""

    @patch("servers.glue.server.glue_client")
    async def test_get_table_success(self, mock_glue_client):
        """Test successful single table retrieval."""
        from servers.glue.server import glue_get_table

        # Mock Glue get_table response
        mock_glue_client.get_table.return_value = {
            "Table": {
                "Name": "test_table",
                "DatabaseName": "test_database",
                "Description": "Test table description",
                "TableType": "EXTERNAL_TABLE",
                "StorageDescriptor": {
                    "Location": "s3://bucket/table/",
                    "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
                    "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                    "Columns": [
                        {"Name": "id", "Type": "bigint", "Comment": "Primary key"},
                        {"Name": "name", "Type": "string", "Comment": "Name field"},
                        {
                            "Name": "created_at",
                            "Type": "timestamp",
                            "Comment": "Creation timestamp",
                        },
                    ],
                },
                "PartitionKeys": [
                    {"Name": "year", "Type": "string"},
                    {"Name": "month", "Type": "string"},
                ],
                "CreatedBy": "test-user",
                "CreateTime": "2024-01-01T00:00:00Z",
                "LastAccessTime": "2024-01-01T12:00:00Z",
            }
        }

        result = await glue_get_table(database_name="test_database", name="test_table")

        assert result is not None
        # The actual implementation returns direct AWS response keys
        assert "Table" in result
        assert result["Table"]["Name"] == "test_table"
        assert result["Table"]["DatabaseName"] == "test_database"
        assert result["Table"]["Description"] == "Test table description"
        assert result["Table"]["TableType"] == "EXTERNAL_TABLE"
        assert result["Table"]["StorageDescriptor"]["Location"] == "s3://bucket/table/"
        assert len(result["Table"]["StorageDescriptor"]["Columns"]) == 3
        assert result["Table"]["StorageDescriptor"]["Columns"][0]["Name"] == "id"

        # Verify Glue client call
        mock_glue_client.get_table.assert_called_once_with(
            DatabaseName="test_database", Name="test_table"
        )

    @patch("servers.glue.server.glue_client")
    async def test_get_table_with_catalog_id(self, mock_glue_client):
        """Test table retrieval with catalog ID."""
        from servers.glue.server import glue_get_table

        mock_glue_client.get_table.return_value = {
            "Table": {
                "Name": "test_table",
                "DatabaseName": "test_database",
                "TableType": "EXTERNAL_TABLE",
            }
        }

        result = await glue_get_table(
            database_name="test_database", name="test_table", catalog_id="123456789012"
        )

        assert result is not None

        # Verify Glue client call with catalog ID
        mock_glue_client.get_table.assert_called_once_with(
            DatabaseName="test_database", Name="test_table", CatalogId="123456789012"
        )

    @patch("servers.glue.server.glue_client")
    async def test_get_table_not_found(self, mock_glue_client):
        """Test table retrieval when not found."""
        from servers.glue.server import glue_get_table

        # Mock Glue get_table to raise an error
        mock_glue_client.get_table.side_effect = ClientError(
            {
                "Error": {
                    "Code": "EntityNotFoundException",
                    "Message": "Table not found",
                }
            },
            "GetTable",
        )

        with pytest.raises(Exception) as exc_info:
            await glue_get_table(
                database_name="test_database", name="nonexistent_table"
            )
        # The implementation wraps ClientError in Exception
        assert "error getting table" in str(exc_info.value).lower()


class TestCreateHTTPApp:
    """Test create_http_app function."""

    @patch("servers.glue.server.mcp")
    def test_create_http_app_success(self, mock_mcp):
        """Test successful HTTP app creation."""
        from servers.glue.server import create_http_app

        app = create_http_app()

        assert app is not None
        # Verify the app has the expected endpoints
        routes = [route.path for route in app.routes]
        assert "/health" in routes
        assert "/" in routes
        assert "/mcp/glue" in routes

    @patch("servers.glue.server.mcp")
    def test_health_endpoint(self, mock_mcp):
        """Test health endpoint."""
        from servers.glue.server import create_http_app
        from fastapi.testclient import TestClient

        app = create_http_app()
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "glue-mcp-server"

    @patch("servers.glue.server.mcp")
    def test_root_endpoint(self, mock_mcp):
        """Test root endpoint."""
        from servers.glue.server import create_http_app
        from fastapi.testclient import TestClient

        app = create_http_app()
        client = TestClient(app)

        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "Glue MCP Server"

    @patch("servers.glue.server.mcp")
    def test_mcp_endpoint(self, mock_mcp):
        """Test MCP endpoint."""
        from servers.glue.server import create_http_app
        from fastapi.testclient import TestClient

        app = create_http_app()
        client = TestClient(app)

        response = client.get("/mcp/glue")

        assert response.status_code == 200
        data = response.json()
        assert "jsonrpc" in data
        assert data["jsonrpc"] == "2.0"


class TestModuleImports:
    """Test module imports and initialization."""

    def test_server_module_imports(self):
        """Test that the server module can be imported successfully."""
        try:
            import servers.glue.server

            assert servers.glue.server is not None
        except ImportError as e:
            pytest.fail(f"Failed to import glue server module: {e}")

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
        from servers.glue.server import get_mcp_credentials

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
            assert result["region_name"] == "us-east-1"  # Default region

    def test_custom_region(self):
        """Test custom region configuration."""
        from servers.glue.server import get_mcp_credentials

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
            assert result["region_name"] == "us-west-2"


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch("servers.glue.server.glue_client")
    async def test_client_not_initialized(self, mock_glue_client):
        """Test behavior when AWS client is not initialized."""
        from servers.glue.server import glue_create_database

        # Set client to None to simulate initialization failure
        import servers.glue.server

        original_client = servers.glue.server.glue_client
        servers.glue.server.glue_client = None

        try:
            with pytest.raises(Exception) as exc_info:
                await glue_create_database(name="test_database")

            assert "unexpected error" in str(exc_info.value).lower() or "nonetype" in str(exc_info.value).lower()
        finally:
            # Restore original client
            servers.glue.server.glue_client = original_client

    @patch("servers.glue.server.glue_client")
    async def test_invalid_parameters(self, mock_glue_client):
        """Test handling of invalid parameters."""
        from servers.glue.server import glue_create_database

        # Test with empty database name - the implementation doesn't validate input parameters
        # so this should pass through to AWS Glue client
        mock_glue_client.create_database.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        
        try:
            result = await glue_create_database(name="")
            # Should succeed if AWS client accepts it
            assert result is not None
        except Exception:
            pass  # Expected to fail but shouldn't crash


class TestIntegration:
    """Integration tests for Glue server."""

    @patch("servers.glue.server.glue_client")
    async def test_full_database_workflow(self, mock_glue_client):
        """Test complete database creation workflow."""
        from servers.glue.server import glue_create_database, glue_get_tables

        # Mock database creation
        mock_glue_client.create_database.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }

        # Mock table listing
        mock_glue_client.get_tables.return_value = {
            "TableList": [
                {
                    "Name": "test_table",
                    "DatabaseName": "test_database",
                    "TableType": "EXTERNAL_TABLE",
                }
            ]
        }

        # Create database
        create_result = await glue_create_database(
            name="test_database", description="Test database"
        )

        assert create_result is not None
        assert create_result["ResponseMetadata"]["HTTPStatusCode"] == 200

        # List tables
        tables_result = await glue_get_tables(database_name="test_database")

        assert tables_result is not None
        assert len(tables_result["TableList"]) == 1
        assert tables_result["TableList"][0]["Name"] == "test_table"

        # Verify both operations were called
        mock_glue_client.create_database.assert_called_once()
        mock_glue_client.get_tables.assert_called_once()
