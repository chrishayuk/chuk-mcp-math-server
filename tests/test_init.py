"""Tests for __init__.py package utilities."""

from chuk_mcp_math_server import __version__


class TestPackageInfo:
    """Test package information."""

    def test_version_available(self):
        """Test that version is available."""
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0


class TestConvenienceFunctions:
    """Test convenience server startup functions."""

    def test_run_server_stdio_import(self):
        """Test that run_server_stdio function exists."""
        from chuk_mcp_math_server import run_server_stdio

        assert callable(run_server_stdio)

    def test_run_server_http_import(self):
        """Test that run_server_http function exists."""
        from chuk_mcp_math_server import run_server_http

        assert callable(run_server_http)

    def test_run_server_stdio_execution(self):
        """Test run_server_stdio creates and runs server."""
        from unittest.mock import patch

        from chuk_mcp_math_server import run_server_stdio

        with patch("chuk_mcp_math_server.create_math_server") as mock_create:
            mock_server = mock_create.return_value

            try:
                # This will block, so we need to mock the run method
                with patch.object(mock_server, "run", side_effect=KeyboardInterrupt):
                    run_server_stdio(function_allowlist=["add"])
            except KeyboardInterrupt:
                pass

            # Verify server was created with correct config
            mock_create.assert_called_once_with(
                transport="stdio", function_allowlist=["add"]
            )

    def test_run_server_http_execution(self):
        """Test run_server_http creates and runs server."""
        from unittest.mock import patch

        from chuk_mcp_math_server import run_server_http

        with patch("chuk_mcp_math_server.create_math_server") as mock_create:
            mock_server = mock_create.return_value

            try:
                with patch.object(mock_server, "run", side_effect=KeyboardInterrupt):
                    run_server_http(port=9000, host="127.0.0.1")
            except KeyboardInterrupt:
                pass

            # Verify server was created with correct config
            mock_create.assert_called_once_with(
                transport="http", port=9000, host="127.0.0.1"
            )
