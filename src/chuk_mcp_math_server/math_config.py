#!/usr/bin/env python3
# src/chuk_mcp_math_server/math_config.py
"""
Math-specific configuration that extends the base ServerConfig.
"""

import logging
import os
from typing import Optional

from .config import ServerConfig

logger = logging.getLogger(__name__)


class MathServerConfig(ServerConfig):
    """Math-specific server configuration with math domain defaults."""

    @classmethod
    def from_env(cls) -> "MathServerConfig":
        """Load math configuration from environment variables with math-specific prefixes."""
        # First load generic config
        base_config = super().from_env()
        config_dict = base_config.model_dump()

        # Then check for math-specific environment variables (backward compatibility)
        math_env_mapping: dict[
            str, str | tuple[str, type | type[int] | type[float]]
        ] = {
            "MCP_MATH_TRANSPORT": "transport",
            "MCP_MATH_PORT": ("port", int),
            "MCP_MATH_HOST": "host",
            "MCP_MATH_CACHE_STRATEGY": "cache_strategy",
            "MCP_MATH_CACHE_SIZE": ("cache_size", int),
            "MCP_MATH_LOG_LEVEL": "log_level",
            "MCP_MATH_TIMEOUT": ("computation_timeout", float),
            "MCP_MATH_MAX_CONCURRENT": ("max_concurrent_calls", int),
        }

        # Handle boolean and list conversions separately
        bool_env_mapping = {
            "MCP_MATH_ENABLE_TOOLS": "enable_tools",
            "MCP_MATH_ENABLE_PROMPTS": "enable_prompts",
            "MCP_MATH_ENABLE_RESOURCES": "enable_resources",
        }

        list_env_mapping = {
            "MCP_MATH_FUNCTION_ALLOWLIST": "function_allowlist",
            "MCP_MATH_FUNCTION_DENYLIST": "function_denylist",
            "MCP_MATH_DOMAIN_ALLOWLIST": "domain_allowlist",
            "MCP_MATH_DOMAIN_DENYLIST": "domain_denylist",
            "MCP_MATH_CATEGORY_ALLOWLIST": "category_allowlist",
            "MCP_MATH_CATEGORY_DENYLIST": "category_denylist",
        }

        # Override with math-specific environment variables if they exist
        for env_key, config_field in math_env_mapping.items():
            if env_key in os.environ:
                if isinstance(config_field, tuple):
                    field_name, converter = config_field
                    try:
                        config_dict[field_name] = converter(os.environ[env_key])
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid value for {env_key}: {e}")
                else:
                    config_dict[config_field] = os.environ[env_key]

        # Handle boolean conversions
        for env_key, field_name in bool_env_mapping.items():
            if env_key in os.environ:
                config_dict[field_name] = os.environ[env_key].lower() == "true"

        # Handle list conversions
        for env_key, field_name in list_env_mapping.items():
            if env_key in os.environ:
                config_dict[field_name] = os.environ[env_key].split(",")

        return cls(**config_dict)


def load_math_configuration_from_sources(
    config_file: Optional[str] = None, cli_overrides: Optional[dict] = None
) -> MathServerConfig:
    """Load math configuration from multiple sources with proper precedence.

    Priority order:
    1. CLI arguments (highest priority)
    2. Math-specific environment variables (MCP_MATH_*)
    3. Generic environment variables (MCP_SERVER_*)
    4. Configuration file
    5. Math defaults (lowest priority)
    """

    # Start with file-based config or defaults
    if config_file:
        base_config = ServerConfig.from_file(config_file)
        base_dict = base_config.model_dump()
    else:
        base_dict = {}

    # Override with environment variables (both generic and math-specific)
    try:
        env_config = MathServerConfig.from_env()
        # Only use non-default values from environment
        for key, value in env_config.model_dump().items():
            env_value = os.getenv(f"MCP_MATH_{key.upper()}") or os.getenv(
                f"MCP_SERVER_{key.upper()}"
            )
            if env_value is not None:
                base_dict[key] = value
        logger.debug("Applied environment variable overrides")
    except Exception as e:
        logger.warning(f"Error loading environment config: {e}")

    # Apply CLI overrides (highest priority)
    if cli_overrides:
        base_dict.update(cli_overrides)
        logger.debug("Applied CLI overrides")

    return MathServerConfig(**base_dict)
