"""Tests for version handling in __init__.py."""


class TestVersionHandling:
    """Test version handling functionality."""

    def test_version_is_string(self):
        """Test that version is a valid string."""
        from amazon_datazone_mcp_server import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0
        # Version should not be empty or just whitespace
        assert __version__.strip() != ""

    def test_version_format(self):
        """Test that version follows expected format."""
        from amazon_datazone_mcp_server import __version__

        # Version should not be "unknown" in normal circumstances
        # (unless VERSION file is missing)
        if __version__ != "unknown":
            # Should have at least one number
            assert any(char.isdigit() for char in __version__)

    def test_version_consistency_across_imports(self):
        """Test that version is consistent across multiple imports."""
        from amazon_datazone_mcp_server import __version__ as version1

        # Import again and verify it's the same
        from amazon_datazone_mcp_server import __version__ as version2

        assert version1 == version2
