"""Tests for configuration functionality."""

import json
import tempfile

import yaml
from pathlib import Path

from chuk_mcp_math_server import MathServerConfig, ServerConfig
from chuk_mcp_math_server.config import load_configuration_from_sources
from chuk_mcp_math_server.math_config import load_math_configuration_from_sources


class TestServerConfig:
    """Test basic server configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ServerConfig()

        assert config.transport == "stdio"
        assert config.port == 8000
        assert config.host == "0.0.0.0"
        assert config.log_level == "INFO"
        assert config.enable_tools
        assert config.enable_resources
        assert config.enable_prompts

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ServerConfig(
            transport="http", port=9000, host="127.0.0.1", log_level="DEBUG"
        )

        assert config.transport == "http"
        assert config.port == 9000
        assert config.host == "127.0.0.1"
        assert config.log_level == "DEBUG"

    def test_config_to_dict(self):
        """Test converting configuration to dictionary."""
        config = ServerConfig(transport="http", port=9000)
        config_dict = config.model_dump()

        assert isinstance(config_dict, dict)
        assert config_dict["transport"] == "http"
        assert config_dict["port"] == 9000

    def test_config_from_dict(self):
        """Test creating configuration from dictionary."""
        data = {"transport": "http", "port": 9000, "log_level": "DEBUG"}
        config = ServerConfig(**data)

        assert config.transport == "http"
        assert config.port == 9000
        assert config.log_level == "DEBUG"


class TestMathServerConfig:
    """Test math-specific configuration."""

    def test_default_math_config(self):
        """Test default math server configuration."""
        config = MathServerConfig()

        # Default filter lists are empty lists, not None
        assert config.function_allowlist == []
        assert config.function_denylist == []
        assert config.domain_allowlist == []
        assert config.domain_denylist == []
        assert config.category_allowlist == []
        assert config.category_denylist == []

    def test_function_filtering_config(self):
        """Test function filtering configuration."""
        config = MathServerConfig(
            function_allowlist=["add", "subtract"], function_denylist=["multiply"]
        )

        assert config.function_allowlist == ["add", "subtract"]
        assert config.function_denylist == ["multiply"]

    def test_domain_filtering_config(self):
        """Test domain filtering configuration."""
        config = MathServerConfig(
            domain_allowlist=["arithmetic"], domain_denylist=["trigonometry"]
        )

        assert config.domain_allowlist == ["arithmetic"]
        assert config.domain_denylist == ["trigonometry"]

    def test_category_filtering_config(self):
        """Test category filtering configuration."""
        config = MathServerConfig(
            category_allowlist=["core"], category_denylist=["advanced"]
        )

        assert config.category_allowlist == ["core"]
        assert config.category_denylist == ["advanced"]


class TestConfigurationLoading:
    """Test configuration file loading."""

    def test_load_from_json_file(self):
        """Test loading configuration from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "transport": "http",
                "port": 9000,
                "function_allowlist": ["add", "subtract"],
            }
            json.dump(config_data, f)
            temp_path = f.name

        try:
            config = load_math_configuration_from_sources(config_file=temp_path)

            assert config.transport == "http"
            assert config.port == 9000
            assert config.function_allowlist == ["add", "subtract"]
        finally:
            Path(temp_path).unlink()

    def test_load_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "transport": "http",
                "port": 9000,
                "domain_allowlist": ["arithmetic"],
            }
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = load_math_configuration_from_sources(config_file=temp_path)

            assert config.transport == "http"
            assert config.port == 9000
            assert config.domain_allowlist == ["arithmetic"]
        finally:
            Path(temp_path).unlink()

    def test_cli_overrides(self):
        """Test CLI overrides take precedence."""
        config = load_math_configuration_from_sources(
            cli_overrides={"transport": "stdio", "function_allowlist": ["add"]}
        )

        assert config.transport == "stdio"
        assert config.function_allowlist == ["add"]

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            # Create and save config
            config1 = MathServerConfig(
                transport="http", port=9000, function_allowlist=["add", "multiply"]
            )
            config1.save_to_file(temp_path)

            # Load it back
            config2 = MathServerConfig.from_file(temp_path)

            assert config2.transport == "http"
            assert config2.port == 9000
            assert config2.function_allowlist == ["add", "multiply"]
        finally:
            Path(temp_path).unlink()

    def test_save_and_load_json_config(self):
        """Test saving and loading JSON configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            # Create and save config as JSON
            config1 = MathServerConfig(
                transport="http", port=9001, function_allowlist=["subtract"]
            )
            config1.save_to_file(temp_path)

            # Load it back
            config2 = MathServerConfig.from_file(temp_path)

            assert config2.transport == "http"
            assert config2.port == 9001
            assert config2.function_allowlist == ["subtract"]
        finally:
            Path(temp_path).unlink()

    def test_load_configuration_without_file(self):
        """Test loading configuration without a config file."""
        config = load_configuration_from_sources(
            config_file=None, env_overrides=False, cli_overrides={"port": 9999}
        )

        assert config.port == 9999
        assert config.transport == "stdio"  # Default


class TestConfigEdgeCases:
    """Test configuration edge cases and error handling."""

    def test_config_from_nonexistent_file(self):
        """Test loading from nonexistent file raises error."""
        import pytest

        with pytest.raises(FileNotFoundError):
            ServerConfig.from_file("/nonexistent/path/config.yaml")

    def test_config_from_unsupported_format(self):
        """Test loading from unsupported file format raises error."""
        import pytest

        temp_path = tempfile.mktemp(suffix=".txt")
        try:
            Path(temp_path).write_text("some config")

            with pytest.raises(ValueError, match="Unsupported config file format"):
                ServerConfig.from_file(temp_path)
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()

    def test_save_to_unsupported_format(self):
        """Test saving to unsupported file format raises error."""
        import pytest

        config = ServerConfig()
        temp_path = tempfile.mktemp(suffix=".txt")

        try:
            with pytest.raises(ValueError, match="Unsupported config file format"):
                config.save_to_file(temp_path)
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()

    def test_config_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("MCP_SERVER_TRANSPORT", "http")
        monkeypatch.setenv("MCP_SERVER_PORT", "9000")
        monkeypatch.setenv("MCP_SERVER_HOST", "127.0.0.1")
        monkeypatch.setenv("MCP_SERVER_LOG_LEVEL", "DEBUG")

        config = ServerConfig.from_env()

        assert config.transport == "http"
        assert config.port == 9000
        assert config.host == "127.0.0.1"
        assert config.log_level == "DEBUG"

    def test_config_validation_port_range(self):
        """Test that port validation works."""
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ServerConfig(port=70000)  # Port too high

        with pytest.raises(ValidationError):
            ServerConfig(port=0)  # Port too low

    def test_config_validation_cache_size(self):
        """Test that cache_size validation works."""
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ServerConfig(cache_size=-1)  # Negative cache size

    def test_load_configuration_with_all_sources(self, tmp_path, monkeypatch):
        """Test loading with file, env, and CLI overrides."""
        from chuk_mcp_math_server.config import load_configuration_from_sources

        # Create config file
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            yaml.dump({"transport": "stdio", "port": 8000, "host": "0.0.0.0"})
        )

        # Set environment variable
        monkeypatch.setenv("MCP_SERVER_PORT", "9000")

        # CLI overrides
        cli_overrides = {"port": 10000, "log_level": "DEBUG"}

        config = load_configuration_from_sources(
            config_file=str(config_file),
            env_overrides=True,
            cli_overrides=cli_overrides,
        )

        # CLI should win
        assert config.port == 10000
        assert config.log_level == "DEBUG"
        # File value should be used for transport
        assert config.transport == "stdio"


class TestMathConfigEnvironment:
    """Test math-specific environment variable handling."""

    def test_math_config_from_env_basic(self, monkeypatch):
        """Test loading math config from environment variables."""
        monkeypatch.setenv("MCP_MATH_TRANSPORT", "http")
        monkeypatch.setenv("MCP_MATH_PORT", "9001")
        monkeypatch.setenv("MCP_MATH_CACHE_SIZE", "2000")

        config = MathServerConfig.from_env()

        assert config.transport == "http"
        assert config.port == 9001
        assert config.cache_size == 2000

    def test_math_config_from_env_booleans(self, monkeypatch):
        """Test boolean environment variable handling."""
        monkeypatch.setenv("MCP_MATH_ENABLE_TOOLS", "true")
        monkeypatch.setenv("MCP_MATH_ENABLE_PROMPTS", "false")

        config = MathServerConfig.from_env()

        assert config.enable_tools is True
        assert config.enable_prompts is False

    def test_math_config_from_env_lists(self, monkeypatch):
        """Test list environment variable handling."""
        monkeypatch.setenv("MCP_MATH_FUNCTION_ALLOWLIST", "add,subtract,multiply")
        monkeypatch.setenv("MCP_MATH_DOMAIN_ALLOWLIST", "arithmetic,number_theory")

        config = MathServerConfig.from_env()

        assert config.function_allowlist == ["add", "subtract", "multiply"]
        assert config.domain_allowlist == ["arithmetic", "number_theory"]

    def test_math_config_env_invalid_values(self, monkeypatch):
        """Test handling of invalid environment variable values."""
        monkeypatch.setenv("MCP_MATH_PORT", "invalid_port")

        # Should handle invalid values gracefully
        config = MathServerConfig.from_env()
        # Port should remain default since conversion failed
        assert isinstance(config.port, int)

    def test_math_config_sets_defaults(self):
        """Test that MathServerConfig sets math-specific defaults."""
        config = MathServerConfig()

        assert config.server_name == "chuk-mcp-math-server"
        assert "mathematical" in config.server_description.lower()

    def test_load_math_configuration_with_cli_overrides(self):
        """Test loading math configuration with CLI overrides."""
        cli_overrides = {
            "function_allowlist": ["add", "subtract"],
            "cache_size": 500,
        }

        config = load_math_configuration_from_sources(cli_overrides=cli_overrides)

        assert config.function_allowlist == ["add", "subtract"]
        assert config.cache_size == 500

    def test_load_math_configuration_with_env_error(self, monkeypatch):
        """Test that env loading errors are handled gracefully."""
        from unittest.mock import patch

        # Mock from_env to raise an exception
        with patch(
            "chuk_mcp_math_server.math_config.MathServerConfig.from_env",
            side_effect=ValueError("Test error"),
        ):
            config = load_math_configuration_from_sources()

            # Should still work with defaults
            assert isinstance(config, MathServerConfig)
