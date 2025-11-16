#!/usr/bin/env python3
# src/chuk_mcp_math_server/config.py
"""
Server configuration management using Pydantic.
"""

import json
import logging
import os
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ServerConfig(BaseModel):
    """Comprehensive server configuration with all customization options."""

    # Transport settings
    transport: Literal["stdio", "http"] = "stdio"
    port: int = Field(default=8000, ge=1, le=65535)
    host: str = "0.0.0.0"

    # Global feature toggles
    enable_tools: bool = True
    enable_prompts: bool = True
    enable_resources: bool = True

    # Function filtering
    function_allowlist: list[str] = Field(default_factory=list)
    function_denylist: list[str] = Field(default_factory=list)
    domain_allowlist: list[str] = Field(default_factory=list)
    domain_denylist: list[str] = Field(default_factory=list)
    category_allowlist: list[str] = Field(default_factory=list)
    category_denylist: list[str] = Field(default_factory=list)

    # Performance settings
    cache_strategy: Literal["none", "memory", "smart"] = "smart"
    cache_size: int = Field(default=1000, ge=0)
    max_concurrent_calls: int = Field(default=10, ge=1)
    computation_timeout: float = Field(default=30.0, ge=0)

    # Logging and debugging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    verbose: bool = False
    quiet: bool = False

    # Security settings
    enable_cors: bool = True
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = Field(default=60, ge=1)

    # Server metadata
    server_name: str = "chuk-mcp-math-server"
    server_description: str = "Configurable mathematical computation server"

    model_config = {
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
    }

    @classmethod
    def from_file(cls, config_path: str | Path) -> "ServerConfig":
        """Load configuration from file (YAML or JSON)."""
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r") as f:
            if path.suffix.lower() in [".yml", ".yaml"]:
                data = yaml.safe_load(f)
            elif path.suffix.lower() == ".json":
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {path.suffix}")

        return cls(**data)

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load configuration from environment variables."""
        env_mapping = {
            "MCP_SERVER_TRANSPORT": "transport",
            "MCP_SERVER_PORT": ("port", int),
            "MCP_SERVER_HOST": "host",
            "MCP_SERVER_LOG_LEVEL": "log_level",
            "MCP_SERVER_CACHE_STRATEGY": "cache_strategy",
            "MCP_SERVER_CACHE_SIZE": ("cache_size", int),
            "MCP_SERVER_NAME": "server_name",
        }

        config_dict = {}
        for env_var, field_info in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                if isinstance(field_info, tuple):
                    field_name, converter = field_info
                    config_dict[field_name] = converter(value)
                else:
                    config_dict[field_info] = value

        return cls(**config_dict)

    def save_to_file(self, config_path: str | Path) -> None:
        """Save configuration to file (YAML or JSON)."""
        path = Path(config_path)

        with open(path, "w") as f:
            if path.suffix.lower() in [".yml", ".yaml"]:
                yaml.dump(
                    self.model_dump(), f, default_flow_style=False, sort_keys=False
                )
            elif path.suffix.lower() == ".json":
                json.dump(self.model_dump(), f, indent=2)
            else:
                raise ValueError(f"Unsupported config file format: {path.suffix}")


def load_configuration_from_sources(
    config_file: Optional[str | Path] = None,
    env_overrides: bool = True,
    cli_overrides: Optional[dict] = None,
) -> ServerConfig:
    """Load configuration from multiple sources with priority ordering.

    Priority (highest to lowest):
    1. CLI overrides
    2. Environment variables
    3. Configuration file
    4. Defaults
    """
    # Start with file-based config or defaults
    if config_file:
        config = ServerConfig.from_file(config_file)
        base_dict = config.model_dump()
    else:
        base_dict = {}

    # Apply environment overrides
    if env_overrides:
        env_config = ServerConfig.from_env()
        env_dict = {k: v for k, v in env_config.model_dump().items() if k in os.environ}
        base_dict.update(env_dict)

    # Apply CLI overrides (highest priority)
    if cli_overrides:
        base_dict.update(cli_overrides)

    return ServerConfig(**base_dict)
