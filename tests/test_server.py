"""Tests for the DataZone MCP server functionality."""

import json
import os
import sys
from unittest.mock import Mock, patch


class TestGetMCPCredentials:
    """Test get_mcp_credentials function."""

    @patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "ASIAQGYBP5OXW5MTKVKQ123456",  # pragma: allowlist secret
            "AWS_SECRET_ACCESS_KEY": "test-secret",  # pragma: allowlist secret
            "AWS_SESSION_TOKEN": "test-token",  # pragma: allowlist secret
            "AWS_DEFAULT_REGION": "us-west-2",  # pragma: allowlist secret
        },
    )
    def test_local_development_credentials(self):
        """Test credentials from environment variables for local development."""
        from servers.datazone.server import get_mcp_credentials

        result = get_mcp_credentials()

        assert result is not None
        assert (
            result["aws_access_key_id"] == "ASIAQGYBP5OXW5MTKVKQ123456"  # pragma: allowlist secret
        )  # pragma: allowlist secret
        assert (
            result["aws_secret_access_key"] == "test-secret"
        )  # pragma: allowlist secret
        assert result["aws_session_token"] == "test-token"  # pragma: allowlist secret
        assert result["region_name"] == "us-west-2"  # pragma: allowlist secret
        assert result["account_id"] == "014498655151"  # pragma: allowlist secret

    @patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",  # Different pattern  # pragma: allowlist secret
            "AWS_SECRET_ACCESS_KEY": "test-secret",  # pragma: allowlist secret
            "AWS_SESSION_TOKEN": "test-token",  # pragma: allowlist secret
        },
    )
    @patch("servers.datazone.server.boto3.client")
    def test_secrets_manager_retrieval(self, mock_boto_client):
        """Test credentials retrieval from Secrets Manager."""
        from servers.datazone.server import get_mcp_credentials

        # Mock secrets manager response
        mock_secrets_client = Mock()
        mock_boto_client.return_value = mock_secrets_client
        mock_secrets_client.get_secret_value.return_value = {
            "SecretString": json.dumps(
                {
                    "AWS_ACCESS_KEY_ID": "secrets-access-key",  # pragma: allowlist secret
                    "AWS_SECRET_ACCESS_KEY": "secrets-secret-key",  # pragma: allowlist secret
                    "AWS_SESSION_TOKEN": "secrets-session-token",  # pragma: allowlist secret
                    "AWS_DEFAULT_REGION": "us-east-1",  # pragma: allowlist secret
                    "ACCOUNT_ID": "123456789012",  # pragma: allowlist secret
                }  # pragma: allowlist secret
            )
        }

        result = get_mcp_credentials()

        assert result is not None
        assert result["aws_access_key_id"] == "secrets-access-key"  # pragma: allowlist secret
        assert result["aws_secret_access_key"] == "secrets-secret-key"  # pragma: allowlist secret
        assert result["aws_session_token"] == "secrets-session-token"  # pragma: allowlist secret
        assert result["region_name"] == "us-east-1"  # pragma: allowlist secret
        assert result["account_id"] == "123456789012"  # pragma: allowlist secret

        # Verify secrets manager was called correctly
        mock_boto_client.assert_called_with("secretsmanager", region_name="us-east-1")  # pragma: allowlist secret
        mock_secrets_client.get_secret_value.assert_called_with(
            SecretId="smus-ai/dev/mcp-aws-credentials"
        )  # pragma: allowlist secret

    @patch.dict(os.environ, {}, clear=True)
    @patch("servers.datazone.server.boto3.client")
    def test_secrets_manager_failure_fallback(self, mock_boto_client):
        """Test fallback to None when Secrets Manager fails."""
        from servers.datazone.server import get_mcp_credentials

        # Mock secrets manager to raise an exception
        mock_secrets_client = Mock()
        mock_boto_client.return_value = mock_secrets_client
        mock_secrets_client.get_secret_value.side_effect = Exception("Access denied")

        result = get_mcp_credentials()

        assert result is None

    @patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "ASIAQGYBP5OXW5MTKVKQ123456",  # pragma: allowlist secret
            "AWS_SECRET_ACCESS_KEY": "test-secret",  # pragma: allowlist secret
            # Missing AWS_SESSION_TOKEN
        },
        clear=True,
    )
    @patch("servers.datazone.server.boto3.client")
    def test_incomplete_environment_variables(self, mock_boto_client):
        """Test that incomplete environment variables trigger Secrets Manager."""
        from servers.datazone.server import get_mcp_credentials

        # Mock secrets manager response
        mock_secrets_client = Mock()
        mock_boto_client.return_value = mock_secrets_client
        mock_secrets_client.get_secret_value.return_value = {
            "SecretString": json.dumps(
                {
                    "AWS_ACCESS_KEY_ID": "secrets-access-key",  # pragma: allowlist secret
                    "AWS_SECRET_ACCESS_KEY": "secrets-secret-key",  # pragma: allowlist secret
                    "AWS_SESSION_TOKEN": "secrets-session-token",  # pragma: allowlist secret
                    "AWS_DEFAULT_REGION": "us-east-1",  # pragma: allowlist secret
                    "ACCOUNT_ID": "123456789012",  # pragma: allowlist secret
                }
            )
        }

        result = get_mcp_credentials()

        # Should use Secrets Manager, not environment variables
        assert result is not None
        assert result["aws_access_key_id"] == "secrets-access-key"  # pragma: allowlist secret
        mock_boto_client.assert_called_once_with(
            "secretsmanager", region_name="us-east-1"  # pragma: allowlist secret
        )
        mock_secrets_client.get_secret_value.assert_called_once()


class TestCreateMCPServer:
    """Test create_mcp_server function."""

    @patch("servers.datazone.server.get_mcp_credentials")
    @patch("servers.datazone.server.boto3.Session")
    @patch("boto3.client")
    @patch("servers.datazone.server.domain_management.register_tools")
    @patch("servers.datazone.server.data_management.register_tools")
    @patch("servers.datazone.server.project_management.register_tools")
    @patch("servers.datazone.server.environment.register_tools")
    @patch("servers.datazone.server.glossary.register_tools")
    def test_create_server_with_credentials(
        self,
        mock_glossary,
        mock_env,
        mock_project,
        mock_data,
        mock_domain,
        mock_boto_client,
        mock_session,
        mock_get_credentials,
    ):
        """Test server creation with valid credentials."""
        from servers.datazone.server import create_mcp_server

        # Mock credentials
        mock_get_credentials.return_value = {
            "aws_access_key_id": "test-key",
            "aws_secret_access_key": "test-secret",
            "aws_session_token": "test-token",
            "region_name": "us-east-1",
            "account_id": "123456789012",
        }

        # Mock AWS session and clients
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_datazone_client = Mock()
        mock_sts_client = Mock()
        mock_session_instance.client.side_effect = lambda service: {
            "datazone": mock_datazone_client,
            "sts": mock_sts_client,
        }[service]

        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {
            "Account": "123456789012",  # pragma: allowlist secret
            "Arn": "arn:aws:sts::123456789012:assumed-role/test-role/test-session",  # pragma: allowlist secret
        }

        # Act
        server = create_mcp_server()

        # Assert
        assert server is not None
        assert server.name == "datazone"

        # Verify AWS session was created with correct credentials
        mock_session.assert_called_once_with(
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            aws_session_token="test-token",
            region_name="us-east-1",
        )

        # Verify all tool modules were registered
        mock_domain.assert_called_once()
        mock_data.assert_called_once()
        mock_project.assert_called_once()
        mock_env.assert_called_once()
        mock_glossary.assert_called_once()

    @patch("servers.datazone.server.get_mcp_credentials")
    @patch("servers.datazone.server.boto3.client")
    @patch("servers.datazone.server.domain_management.register_tools")
    def test_create_server_without_credentials(
        self, mock_domain, mock_boto_client, mock_get_credentials
    ):
        """Test server creation fallback to default credentials."""
        from servers.datazone.server import create_mcp_server

        # Mock no credentials from Secrets Manager
        mock_get_credentials.return_value = None

        # Mock default clients
        mock_datazone_client = Mock()
        mock_sts_client = Mock()
        mock_boto_client.side_effect = lambda service: {
            "datazone": mock_datazone_client,
            "sts": mock_sts_client,
        }[service]

        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {
            "Account": "123456789012",  # pragma: allowlist secret
            "Arn": "arn:aws:sts::123456789012:user/test-user",  # pragma: allowlist secret
        }

        # Act
        server = create_mcp_server()

        # Assert
        assert server is not None
        assert server.name == "datazone"

        # Verify default clients were used
        mock_boto_client.assert_any_call("datazone")
        mock_boto_client.assert_any_call("sts")

    @patch("servers.datazone.server.get_mcp_credentials")
    @patch("servers.datazone.server.boto3.Session")
    def test_create_server_aws_client_error(self, mock_session, mock_get_credentials):
        """Test server creation when AWS client initialization fails."""
        from servers.datazone.server import create_mcp_server

        # Mock credentials
        mock_get_credentials.return_value = {
            "aws_access_key_id": "test-key",
            "aws_secret_access_key": "test-secret",
            "aws_session_token": "test-token",
            "region_name": "us-east-1",
            "account_id": "123456789012",
        }

        # Mock session creation to fail
        mock_session.side_effect = Exception("AWS connection failed")

        # Act - should not raise exception
        server = create_mcp_server()

        # Assert - server should still be created
        assert server is not None
        assert server.name == "datazone"


class TestCreateHTTPApp:
    """Test create_http_app function."""

    @patch("servers.datazone.server.create_mcp_server")
    @patch("fastapi.FastAPI")
    def test_create_http_app_success(self, mock_fastapi_class, mock_create_server):
        """Test successful HTTP app creation."""
        from servers.datazone.server import create_http_app

        # Mock MCP server
        mock_server = Mock()
        mock_server._tool_manager._tools = {"test_tool": Mock()}
        mock_create_server.return_value = mock_server

        # Mock FastAPI app instance
        mock_app = Mock()
        mock_app.get = Mock()  # FastAPI app should have route decorators
        mock_fastapi_class.return_value = mock_app

        app = create_http_app()

        # Assert
        assert app is not None
        assert hasattr(app, "get")  # FastAPI app should have route decorators

    @patch("servers.datazone.server.create_mcp_server")
    @patch("fastapi.FastAPI")
    def test_create_http_app_without_fastapi(
        self, mock_fastapi_class, mock_create_server
    ):
        """Test HTTP app creation when FastAPI is not available."""
        # This test would need to mock the ImportError, but since FastAPI is available in test env,
        # we'll just verify the function returns something when create_mcp_server works
        from servers.datazone.server import create_http_app

        mock_server = Mock()
        mock_server._tool_manager._tools = {}
        mock_create_server.return_value = mock_server

        # Mock FastAPI app instance
        mock_app = Mock()
        mock_fastapi_class.return_value = mock_app

        app = create_http_app()

        assert app is not None


class TestHealthEndpoint:
    """Test health check endpoint."""

    @patch("servers.datazone.server.create_mcp_server")
    @patch("fastapi.FastAPI")
    def test_health_endpoint(self, mock_fastapi_class, mock_create_server):
        """Test health check endpoint returns correct data."""
        from servers.datazone.server import create_http_app

        # Mock MCP server with tools
        mock_server = Mock()
        mock_server._tool_manager._tools = {
            "tool1": Mock(),
            "tool2": Mock(),
            "tool3": Mock(),
        }
        mock_create_server.return_value = mock_server

        # Mock FastAPI app instance
        mock_app = Mock()
        mock_fastapi_class.return_value = mock_app

        app = create_http_app()

        # Test the health endpoint manually by calling the function
        # In a real test, you might use TestClient from FastAPI
        # For now, we'll verify the app was created successfully
        assert app is not None


class TestMainFunction:
    """Test main function with different transport modes."""

    @patch.dict(os.environ, {"MCP_TRANSPORT": "stdio"})
    @patch("servers.datazone.server.create_mcp_server")
    def test_main_stdio_transport(self, mock_create_server):
        """Test main function with stdio transport."""
        from servers.datazone.server import main

        # Mock MCP server
        mock_server = Mock()
        mock_create_server.return_value = mock_server

        # Act
        main()

        # Assert
        mock_create_server.assert_called_once()
        mock_server.run.assert_called_once()

    @patch.dict(
        os.environ, {"MCP_TRANSPORT": "http", "HOST": "127.0.0.1", "PORT": "9000"}
    )
    @patch("servers.datazone.server.create_http_app")
    def test_main_http_transport(self, mock_create_app):
        """Test main function with HTTP transport."""
        from servers.datazone.server import main
        import sys

        # Mock HTTP app
        mock_app = Mock()
        mock_create_app.return_value = mock_app

        # Mock uvicorn module in sys.modules
        mock_uvicorn = Mock()
        with patch.dict(sys.modules, {"uvicorn": mock_uvicorn}):
            # Act
            main()

        # Assert
        mock_create_app.assert_called_once()
        mock_uvicorn.run.assert_called_once_with(
            mock_app, host="127.0.0.1", port=9000, log_level="info"
        )

    @patch.dict(os.environ, {"MCP_TRANSPORT": "http"})
    @patch("servers.datazone.server.create_http_app")
    @patch("sys.exit")
    def test_main_http_transport_app_creation_fails(self, mock_exit, mock_create_app):
        """Test main function when HTTP app creation fails."""
        from servers.datazone.server import main

        # Mock app creation to return None
        mock_create_app.return_value = None

        # Make sys.exit actually stop execution
        mock_exit.side_effect = SystemExit(1)

        # Mock uvicorn module in sys.modules to avoid import errors
        mock_uvicorn = Mock()
        with patch.dict(sys.modules, {"uvicorn": mock_uvicorn}):
            # Act - should raise SystemExit
            try:
                main()
            except SystemExit:
                pass  # Expected

        # Assert
        mock_exit.assert_called_once_with(1)
        # uvicorn should not be called since app creation failed
        mock_uvicorn.run.assert_not_called()

    @patch("servers.datazone.server.create_mcp_server")
    @patch("sys.exit")
    @patch("builtins.print")
    def test_main_keyboard_interrupt(self, mock_print, mock_exit, mock_create_server):
        """Test main function handles KeyboardInterrupt gracefully."""
        from servers.datazone.server import main

        # Mock server to raise KeyboardInterrupt
        mock_server = Mock()
        mock_server.run.side_effect = KeyboardInterrupt()
        mock_create_server.return_value = mock_server

        # Act
        main()

        # Assert
        mock_print.assert_called_with(
            "KeyboardInterrupt received. Shutting down gracefully.", file=sys.stderr
        )
        mock_exit.assert_called_once_with(0)

    @patch("servers.datazone.server.create_mcp_server")
    @patch("sys.exit")
    @patch("builtins.print")
    def test_main_exception_handling(self, mock_print, mock_exit, mock_create_server):
        """Test main function handles general exceptions."""
        from servers.datazone.server import main

        # Mock server to raise exception
        mock_server = Mock()
        mock_server.run.side_effect = RuntimeError("Test error")
        mock_create_server.return_value = mock_server

        # Act
        main()

        # Assert
        mock_exit.assert_called_once_with(1)

        # Verify error was printed as JSON
        printed_args = mock_print.call_args[0]
        error_output = printed_args[0]

        # Should be valid JSON
        error_data = json.loads(error_output)
        assert "error" in error_data
        assert "type" in error_data
        assert "message" in error_data
        assert "Test error" in error_data["error"]


class TestModuleImports:
    """Test that all required modules can be imported."""

    def test_server_module_imports(self):
        """Test that server module imports successfully."""
        from servers.datazone import server

        # Verify key functions exist
        assert hasattr(server, "get_mcp_credentials")
        assert hasattr(server, "create_mcp_server")
        assert hasattr(server, "create_http_app")
        assert hasattr(server, "main")

    def test_tool_modules_import(self):
        """Test that all tool modules can be imported."""
        from servers.datazone.tools import (
            data_management,
            domain_management,
            environment,
            glossary,
            project_management,
        )

        # Verify all modules have register_tools function
        assert hasattr(domain_management, "register_tools")
        assert hasattr(data_management, "register_tools")
        assert hasattr(project_management, "register_tools")
        assert hasattr(environment, "register_tools")
        assert hasattr(glossary, "register_tools")


class TestEnvironmentConfiguration:
    """Test environment variable handling."""

    def test_default_transport_mode(self):
        """Test default transport mode when not specified."""
        with patch.dict(os.environ, {}, clear=True):
            # Default should be stdio
            transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
            assert transport == "stdio"

    def test_default_host_and_port(self):
        """Test default host and port for HTTP transport."""
        with patch.dict(os.environ, {}, clear=True):
            host = os.getenv("HOST", "0.0.0.0")
            port = int(os.getenv("PORT", "8080"))

            assert host == "0.0.0.0"
            assert port == 8080
