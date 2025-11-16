"""Tests for CLI command line interface."""

import sys
from unittest.mock import patch

import pytest

from chuk_mcp_math_server.cli import (
    args_to_config_overrides,
    check_dependencies,
    create_argument_parser,
    main,
)


class TestArgumentParser:
    """Test argument parser creation and handling."""

    def test_create_argument_parser(self):
        """Test creating argument parser."""
        parser = create_argument_parser()
        assert parser is not None

        # Test parsing basic args
        args = parser.parse_args([])
        assert args.transport == "stdio"
        assert args.port == 8000

    def test_parse_transport_args(self):
        """Test parsing transport arguments."""
        parser = create_argument_parser()

        args = parser.parse_args(["--transport", "http"])
        assert args.transport == "http"

        args = parser.parse_args(["-t", "stdio"])
        assert args.transport == "stdio"

    def test_parse_port_args(self):
        """Test parsing port arguments."""
        parser = create_argument_parser()

        args = parser.parse_args(["--port", "9000"])
        assert args.port == 9000

        args = parser.parse_args(["-p", "8080"])
        assert args.port == 8080

    def test_parse_function_filtering_args(self):
        """Test parsing function filtering arguments."""
        parser = create_argument_parser()

        args = parser.parse_args(["--functions", "add", "subtract"])
        assert args.functions == ["add", "subtract"]

        args = parser.parse_args(["--exclude-functions", "multiply"])
        assert args.exclude_functions == ["multiply"]

    def test_parse_domain_filtering_args(self):
        """Test parsing domain filtering arguments."""
        parser = create_argument_parser()

        args = parser.parse_args(["--domains", "arithmetic"])
        assert args.domains == ["arithmetic"]

        args = parser.parse_args(["--exclude-domains", "trigonometry"])
        assert args.exclude_domains == ["trigonometry"]

    def test_parse_verbose_args(self):
        """Test parsing verbose/quiet arguments."""
        parser = create_argument_parser()

        args = parser.parse_args(["--verbose"])
        assert args.verbose is True

        args = parser.parse_args(["-v"])
        assert args.verbose is True

        args = parser.parse_args(["--quiet"])
        assert args.quiet is True


class TestArgsToConfigOverrides:
    """Test converting arguments to configuration overrides."""

    def test_basic_conversion(self):
        """Test basic argument to config conversion."""
        parser = create_argument_parser()
        args = parser.parse_args(["--transport", "http", "--port", "9000"])

        overrides = args_to_config_overrides(args)

        assert overrides["transport"] == "http"
        assert overrides["port"] == 9000

    def test_function_filtering_conversion(self):
        """Test function filtering argument conversion."""
        parser = create_argument_parser()
        args = parser.parse_args(["--functions", "add", "subtract"])

        overrides = args_to_config_overrides(args)

        assert "function_allowlist" in overrides
        assert overrides["function_allowlist"] == ["add", "subtract"]

    def test_verbose_sets_log_level(self):
        """Test that verbose flag sets log level."""
        parser = create_argument_parser()
        args = parser.parse_args(["--verbose"])

        overrides = args_to_config_overrides(args)

        assert overrides["log_level"] == "DEBUG"

    def test_quiet_sets_log_level(self):
        """Test that quiet flag sets log level."""
        parser = create_argument_parser()
        args = parser.parse_args(["--quiet"])

        overrides = args_to_config_overrides(args)

        assert overrides["log_level"] == "WARNING"

    def test_feature_toggles(self):
        """Test feature toggle argument conversion."""
        parser = create_argument_parser()
        args = parser.parse_args(["--disable-tools"])

        overrides = args_to_config_overrides(args)

        assert overrides["enable_tools"] is False


class TestCheckDependencies:
    """Test dependency checking."""

    def test_check_dependencies_returns_true(self):
        """Test that check_dependencies returns True when deps are available."""
        result = check_dependencies()
        assert result is True


class TestMainFunction:
    """Test main CLI entry point."""

    @patch("chuk_mcp_math_server.cli.run_server")
    def test_main_with_show_config(self, mock_run_server, capsys, monkeypatch):
        """Test main with --show-config flag."""
        monkeypatch.setattr(sys, "argv", ["chuk-mcp-math-server", "--show-config"])

        # This should not raise SystemExit, just return
        main()

        captured = capsys.readouterr()
        assert "Current Configuration" in captured.out

        # Should not have tried to run server
        mock_run_server.assert_not_called()

    @patch("chuk_mcp_math_server.cli.run_server")
    @patch("chuk_mcp_math_server.math_config.MathServerConfig.save_to_file")
    def test_main_with_save_config(
        self, mock_save, mock_run_server, tmp_path, capsys, monkeypatch
    ):
        """Test main with --save-config flag."""
        config_file = str(tmp_path / "test_config.yaml")
        monkeypatch.setattr(
            sys, "argv", ["chuk-mcp-math-server", "--save-config", config_file]
        )

        # This should not raise SystemExit, just return
        main()

        captured = capsys.readouterr()
        assert "Configuration saved" in captured.out

        # Should have called save
        mock_save.assert_called_once()

        # Should not have tried to run server
        mock_run_server.assert_not_called()

    @patch("chuk_mcp_math_server.cli.run_server")
    def test_main_default_stdio(self, mock_run_server, monkeypatch):
        """Test main defaults to stdio transport."""
        monkeypatch.setattr(sys, "argv", ["chuk-mcp-math-server"])

        main()

        # Should have called run_server
        mock_run_server.assert_called_once()

        # Check config passed to run_server
        config = mock_run_server.call_args[0][0]
        assert config.transport == "stdio"

    @patch("chuk_mcp_math_server.cli.run_server")
    def test_main_with_http_transport(self, mock_run_server, monkeypatch):
        """Test main with HTTP transport."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["chuk-mcp-math-server", "--transport", "http", "--port", "9000"],
        )

        main()

        mock_run_server.assert_called_once()

        config = mock_run_server.call_args[0][0]
        assert config.transport == "http"
        assert config.port == 9000

    @patch("chuk_mcp_math_server.cli.run_server")
    def test_main_with_function_filtering(self, mock_run_server, monkeypatch):
        """Test main with function filtering arguments."""
        monkeypatch.setattr(
            sys, "argv", ["chuk-mcp-math-server", "--functions", "add", "subtract"]
        )

        main()

        mock_run_server.assert_called_once()

        config = mock_run_server.call_args[0][0]
        assert config.function_allowlist == ["add", "subtract"]

    @patch("chuk_mcp_math_server.cli.run_server")
    def test_main_with_config_file(self, mock_run_server, tmp_path, monkeypatch):
        """Test main with config file loading."""
        import yaml

        config_file = tmp_path / "test.yaml"
        config_file.write_text(
            yaml.dump({"function_allowlist": ["add", "subtract", "multiply"]})
        )

        monkeypatch.setattr(
            sys, "argv", ["chuk-mcp-math-server", "--config", str(config_file)]
        )

        main()

        mock_run_server.assert_called_once()
        config = mock_run_server.call_args[0][0]
        # CLI defaults override config file for basic settings
        assert config.transport == "stdio"
        assert config.port == 8000
        # Function allowlist from file should be used (not a CLI default)
        assert config.function_allowlist == ["add", "subtract", "multiply"]


class TestRunServer:
    """Test run_server function."""

    def test_run_server_success(self, math_config):
        """Test successful server run."""
        with patch(
            "chuk_mcp_math_server.cli.ConfigurableMCPMathServer"
        ) as mock_server_class:
            mock_server = mock_server_class.return_value

            # Mock the run method to raise KeyboardInterrupt to stop
            mock_server.run.side_effect = KeyboardInterrupt

            from chuk_mcp_math_server.cli import run_server

            # Should handle KeyboardInterrupt gracefully
            run_server(math_config)

            mock_server_class.assert_called_once_with(math_config)
            mock_server.run.assert_called_once()

    def test_run_server_exception(self, math_config):
        """Test server run with exception."""
        with patch(
            "chuk_mcp_math_server.cli.ConfigurableMCPMathServer"
        ) as mock_server_class:
            mock_server = mock_server_class.return_value
            mock_server.run.side_effect = RuntimeError("Test error")

            from chuk_mcp_math_server.cli import run_server

            with pytest.raises(RuntimeError, match="Test error"):
                run_server(math_config)


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_main_with_invalid_config_file(self, monkeypatch, capsys):
        """Test main with invalid config file."""
        monkeypatch.setattr(
            sys, "argv", ["chuk-mcp-math-server", "--config", "/nonexistent/file.yaml"]
        )

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("chuk_mcp_math_server.cli.run_server")
    def test_main_handles_server_exception(self, mock_run_server, monkeypatch):
        """Test that main handles server exceptions."""
        monkeypatch.setattr(sys, "argv", ["chuk-mcp-math-server"])

        mock_run_server.side_effect = RuntimeError("Server failed")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("chuk_mcp_math_server.math_config.MathServerConfig.save_to_file")
    def test_main_save_config_error(self, mock_save, monkeypatch, capsys):
        """Test that save_config error is handled."""
        monkeypatch.setattr(
            sys, "argv", ["chuk-mcp-math-server", "--save-config", "test.yaml"]
        )

        mock_save.side_effect = IOError("Permission denied")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Failed to save configuration" in captured.out


class TestAdvancedFiltering:
    """Test advanced filtering arguments."""

    def test_parse_domain_filtering_args(self):
        """Test parsing domain filtering arguments."""
        from chuk_mcp_math_server.cli import (
            args_to_config_overrides,
            create_argument_parser,
        )

        parser = create_argument_parser()
        args = parser.parse_args(
            ["--domains", "arithmetic", "--exclude-domains", "trigonometry"]
        )
        overrides = args_to_config_overrides(args)

        assert overrides["domain_allowlist"] == ["arithmetic"]
        assert overrides["domain_denylist"] == ["trigonometry"]

    def test_parse_category_filtering_args(self):
        """Test parsing category filtering arguments."""
        from chuk_mcp_math_server.cli import (
            args_to_config_overrides,
            create_argument_parser,
        )

        parser = create_argument_parser()
        args = parser.parse_args(
            ["--categories", "core", "primes", "--exclude-categories", "advanced"]
        )
        overrides = args_to_config_overrides(args)

        assert overrides["category_allowlist"] == ["core", "primes"]
        assert overrides["category_denylist"] == ["advanced"]

    def test_parse_exclude_functions_args(self):
        """Test parsing exclude-functions arguments."""
        from chuk_mcp_math_server.cli import (
            args_to_config_overrides,
            create_argument_parser,
        )

        parser = create_argument_parser()
        args = parser.parse_args(
            ["--exclude-functions", "slow_func", "deprecated_func"]
        )
        overrides = args_to_config_overrides(args)

        assert overrides["function_denylist"] == ["slow_func", "deprecated_func"]


class TestRunServerLogging:
    """Test run_server logging paths."""

    def test_run_server_http_logging(self, capsys):
        """Test that HTTP server logs host and port."""
        from chuk_mcp_math_server import MathServerConfig
        from chuk_mcp_math_server.cli import run_server

        config = MathServerConfig(transport="http", port=9000, host="127.0.0.1")

        with patch(
            "chuk_mcp_math_server.cli.ConfigurableMCPMathServer"
        ) as mock_server_class:
            mock_server = mock_server_class.return_value
            mock_server.run.side_effect = KeyboardInterrupt
            mock_server.get_function_stats.return_value = {
                "total_available": 10,
                "total_filtered": 10,
                "filtering_active": False,
            }

            run_server(config)

            # Should have logged HTTP host:port
            mock_server_class.assert_called_once()

    def test_run_server_no_filtering_logging(self, capsys):
        """Test logging when no filtering is active."""
        from chuk_mcp_math_server import MathServerConfig
        from chuk_mcp_math_server.cli import run_server

        config = MathServerConfig(transport="stdio")

        with patch(
            "chuk_mcp_math_server.cli.ConfigurableMCPMathServer"
        ) as mock_server_class:
            mock_server = mock_server_class.return_value
            mock_server.run.side_effect = KeyboardInterrupt
            mock_server.get_function_stats.return_value = {
                "total_available": 15,
                "total_filtered": 15,
                "filtering_active": False,
            }

            run_server(config)

            # Should log all functions available
            mock_server.get_function_stats.assert_called_once()
