"""Tests for version handling in __init__.py."""

import sys
from unittest.mock import patch


class TestVersionHandling:
    """Test version handling functionality."""

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    def test_version_file_exists(self, mock_read_text, mock_exists):
        """Test version reading when VERSION file exists."""
        # Mock the VERSION file as existing
        mock_exists.return_value = True
        mock_read_text.return_value = "1.0.0\n"

        # Clear module cache
        module_name = "servers.datazone"
        if module_name in sys.modules:
            del sys.modules[module_name]

        # Import should read version from file
        from servers.datazone import __version__

        assert __version__ == "1.0.0"
        mock_exists.assert_called_once()
        mock_read_text.assert_called_once()

    @patch("pathlib.Path.exists")
    def test_version_file_missing(self, mock_exists):
        """Test version handling when VERSION file doesn"t exist - covers line 22."""
        # Mock the VERSION file as not existing
        mock_exists.return_value = False

        # Clear module cache to force re-import
        module_name = "servers.datazone"
        if module_name in sys.modules:
            del sys.modules[module_name]

        # Import should fallback to "unknown"
        from servers.datazone import __version__

        # This should trigger line 22: __version__ = "unknown"
        assert __version__ == "unknown"
        mock_exists.assert_called_once()

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    def test_version_file_read_error(self, mock_read_text, mock_exists):
        """Test version handling when VERSION file exists but can"t be read."""
        # Mock the VERSION file as existing but reading fails
        mock_exists.return_value = True
        mock_read_text.side_effect = FileNotFoundError()

        # Clear module cache
        module_name = "servers.datazone"
        if module_name in sys.modules:
            del sys.modules[module_name]

        # Import should fallback to "unknown" due to read error
        from servers.datazone import __version__

        assert __version__ == "unknown"
