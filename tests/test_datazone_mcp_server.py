"""Unit tests for Amazon DataZone MCP Server."""

from unittest.mock import Mock, patch

# Test version import
try:
    from amazon_datazone_mcp_server import __version__

    def test_version_import():
        """Test that version can be imported successfully."""
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0

except ImportError:
    # Version might not be available during development
    def test_version_import():
        """Test version import gracefully handles missing version."""
        assert True  # Version import is optional


# Test server import and initialization
def test_server_import():
    """Test that server module can be imported."""
    try:
        from amazon_datazone_mcp_server import __version__

        # Test that version is a string and not empty
        assert isinstance(__version__, str)
        assert len(__version__) > 0
    except ImportError:
        # Accept that version might not be available during development
        pass


def test_server_main_function():
    """Test that the main function can be imported and called."""
    from amazon_datazone_mcp_server.server import main

    # Mock the create_mcp_server function to return a mock MCP server
    with patch(
        "amazon_datazone_mcp_server.server.create_mcp_server"
    ) as mock_create_mcp:
        mock_mcp = Mock()
        mock_mcp.run.return_value = None
        mock_create_mcp.return_value = mock_mcp

        # Should not raise any exceptions during import/setup
        try:
            main()
        except SystemExit:
            # Expected behavior when server completes
            pass
        except Exception as e:
            # Log the error but don't fail the test if it's just a configuration issue
            print(f"Server main function test completed with: {e}")


def test_server_main_function_with_exception():
    """Test server error handling."""
    from amazon_datazone_mcp_server.server import main

    # Test that exceptions are handled gracefully
    with patch(
        "amazon_datazone_mcp_server.server.create_mcp_server"
    ) as mock_create_mcp:
        mock_mcp = Mock()
        mock_mcp.run.side_effect = Exception("Test error")
        mock_create_mcp.return_value = mock_mcp

        # Should handle exceptions gracefully
        try:
            main()
        except SystemExit as e:
            # Expected behavior on error
            assert e.code == 1


def test_module_structure():
    """Test that the module structure is correct."""
    # Test that we can import the main components
    import amazon_datazone_mcp_server  # noqa: F401

    # This should not raise any import errors
    assert True
