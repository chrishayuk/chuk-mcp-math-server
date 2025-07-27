#!/usr/bin/env python3
# src/chuk_mcp_math_server/math_config.py
"""
Math-specific configuration that extends the base ServerConfig.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .config import ServerConfig, load_configuration_from_sources

logger = logging.getLogger(__name__)

@dataclass
class MathServerConfig(ServerConfig):
    """Math-specific server configuration with math domain defaults."""
    
    def __post_init__(self):
        # Set math-specific defaults
        if self.server_name == "generic-mcp-server":
            self.server_name = "chuk-mcp-math-server"
        
        if self.server_description == "Configurable MCP server":
            self.server_description = "Configurable mathematical computation server"
        
        # Call parent validation
        super().__post_init__()
    
    @classmethod
    def from_env(cls) -> 'MathServerConfig':
        """Load math configuration from environment variables with math-specific prefixes."""
        # First load generic config
        base_config = super().from_env()
        
        # Then check for math-specific environment variables (backward compatibility)
        math_env_mapping = {
            'MCP_MATH_TRANSPORT': 'transport',
            'MCP_MATH_PORT': ('port', int),
            'MCP_MATH_HOST': 'host',
            'MCP_MATH_ENABLE_TOOLS': ('enable_tools', lambda x: x.lower() == 'true'),
            'MCP_MATH_ENABLE_PROMPTS': ('enable_prompts', lambda x: x.lower() == 'true'),
            'MCP_MATH_ENABLE_RESOURCES': ('enable_resources', lambda x: x.lower() == 'true'),
            'MCP_MATH_FUNCTION_WHITELIST': ('function_whitelist', lambda x: x.split(',')),
            'MCP_MATH_FUNCTION_BLACKLIST': ('function_blacklist', lambda x: x.split(',')),
            'MCP_MATH_DOMAIN_WHITELIST': ('domain_whitelist', lambda x: x.split(',')),
            'MCP_MATH_DOMAIN_BLACKLIST': ('domain_blacklist', lambda x: x.split(',')),
            'MCP_MATH_CACHE_STRATEGY': 'cache_strategy',
            'MCP_MATH_CACHE_SIZE': ('cache_size', int),
            'MCP_MATH_LOG_LEVEL': 'log_level',
            'MCP_MATH_TIMEOUT': ('computation_timeout', float),
            'MCP_MATH_MAX_CONCURRENT': ('max_concurrent_calls', int),
        }
        
        config_data = base_config.to_dict()
        
        # Override with math-specific environment variables if they exist
        for env_key, config_field in math_env_mapping.items():
            if env_key in os.environ:
                if isinstance(config_field, tuple):
                    field_name, converter = config_field
                    try:
                        config_data[field_name] = converter(os.environ[env_key])
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid value for {env_key}: {e}")
                else:
                    config_data[config_field] = os.environ[env_key]
        
        return cls(**config_data)

def load_math_configuration_from_sources(
    config_file: Optional[str] = None,
    cli_overrides: Optional[Dict[str, Any]] = None
) -> MathServerConfig:
    """Load math configuration from multiple sources with proper precedence.
    
    Priority order:
    1. CLI arguments (highest priority)
    2. Math-specific environment variables (MCP_MATH_*)
    3. Generic environment variables (MCP_SERVER_*)
    4. Configuration file
    5. Math defaults (lowest priority)
    """
    
    # Start with math-specific defaults
    config = MathServerConfig()
    
    # Load from file if specified
    if config_file:
        try:
            # Load as base config first, then convert
            file_config = ServerConfig.from_file(config_file)
            file_data = file_config.to_dict()
            
            # Convert to math config
            for key, value in file_data.items():
                if key != "custom_config_path" and hasattr(config, key):
                    setattr(config, key, value)
            
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            raise
    
    # Override with environment variables (both generic and math-specific)
    try:
        env_config = MathServerConfig.from_env()
        for key, value in env_config.to_dict().items():
            if value is not None and value != getattr(MathServerConfig(), key):
                setattr(config, key, value)
        logger.debug("Applied environment variable overrides")
    except Exception as e:
        logger.warning(f"Error loading environment config: {e}")
    
    # Apply CLI overrides (highest priority)
    if cli_overrides:
        for key, value in cli_overrides.items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)
        logger.debug("Applied CLI overrides")
    
    return config