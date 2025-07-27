#!/usr/bin/env python3
# src/chuk_mcp_math_server/config.py
"""
Server configuration management with multiple loading strategies.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

# YAML is always available (included in package dependencies)
import yaml

logger = logging.getLogger(__name__)

def _get_package_version():
    """Get package version dynamically."""
    try:
        from ._version import __version__
        return __version__
    except (ImportError, AttributeError):
        pass
    
    try:
        from importlib.metadata import version, PackageNotFoundError
        return version("chuk-mcp-math-server")
    except (ImportError, PackageNotFoundError):
        pass
    
    return "0.1.0"

@dataclass
class ServerConfig:
    """Comprehensive server configuration with all customization options."""
    
    # Transport settings
    transport: str = "stdio"
    port: int = 8000
    host: str = "0.0.0.0"
    
    # Global feature toggles
    enable_tools: bool = True
    enable_prompts: bool = True
    enable_resources: bool = True
    
    # Function filtering
    function_whitelist: List[str] = field(default_factory=list)
    function_blacklist: List[str] = field(default_factory=list)
    domain_whitelist: List[str] = field(default_factory=list)
    domain_blacklist: List[str] = field(default_factory=list)
    category_whitelist: List[str] = field(default_factory=list)
    category_blacklist: List[str] = field(default_factory=list)
    
    # Performance settings
    cache_strategy: str = "smart"
    cache_size: int = 1000
    max_concurrent_calls: int = 10
    computation_timeout: float = 30.0
    
    # Logging and debugging
    log_level: str = "INFO"
    verbose: bool = False
    quiet: bool = False
    
    # Security settings
    enable_cors: bool = True
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 60
    
    # Server metadata
    server_name: str = "generic-mcp-server"
    server_version: str = field(default_factory=_get_package_version)
    server_description: str = "Configurable MCP server"
    
    # Advanced options
    streaming_threshold: int = 1000
    memory_limit_mb: int = 512
    custom_config_path: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration values."""
        if self.transport not in ["stdio", "http"]:
            raise ValueError(f"Invalid transport: {self.transport}")
        
        if not (1 <= self.port <= 65535):
            raise ValueError(f"Invalid port: {self.port}")
        
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            raise ValueError(f"Invalid log level: {self.log_level}")
        
        if self.cache_strategy not in ["none", "memory", "smart"]:
            raise ValueError(f"Invalid cache strategy: {self.cache_strategy}")
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ServerConfig':
        """Load configuration from file (YAML or JSON)."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            if config_path.suffix.lower() in ['.yml', '.yaml']:
                data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> 'ServerConfig':
        """Load configuration from environment variables."""
        env_mapping = {
            'MCP_SERVER_TRANSPORT': 'transport',
            'MCP_SERVER_PORT': ('port', int),
            'MCP_SERVER_HOST': 'host',
            'MCP_SERVER_ENABLE_TOOLS': ('enable_tools', lambda x: x.lower() == 'true'),
            'MCP_SERVER_ENABLE_PROMPTS': ('enable_prompts', lambda x: x.lower() == 'true'),
            'MCP_SERVER_ENABLE_RESOURCES': ('enable_resources', lambda x: x.lower() == 'true'),
            'MCP_SERVER_FUNCTION_WHITELIST': ('function_whitelist', lambda x: x.split(',')),
            'MCP_SERVER_FUNCTION_BLACKLIST': ('function_blacklist', lambda x: x.split(',')),
            'MCP_SERVER_DOMAIN_WHITELIST': ('domain_whitelist', lambda x: x.split(',')),
            'MCP_SERVER_DOMAIN_BLACKLIST': ('domain_blacklist', lambda x: x.split(',')),
            'MCP_SERVER_CACHE_STRATEGY': 'cache_strategy',
            'MCP_SERVER_CACHE_SIZE': ('cache_size', int),
            'MCP_SERVER_LOG_LEVEL': 'log_level',
            'MCP_SERVER_TIMEOUT': ('computation_timeout', float),
            'MCP_SERVER_MAX_CONCURRENT': ('max_concurrent_calls', int),
        }
        
        config_data = {}
        for env_key, config_field in env_mapping.items():
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
    
    def save_to_file(self, config_path: str, format: str = "yaml"):
        """Save configuration to file."""
        config_data = self.to_dict()
        
        with open(config_path, 'w') as f:
            if format.lower() == "yaml":
                yaml.dump(config_data, f, default_flow_style=False)
            elif format.lower() == "json":
                json.dump(config_data, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")

def load_configuration_from_sources(
    config_file: Optional[str] = None,
    cli_overrides: Optional[Dict[str, Any]] = None
) -> ServerConfig:
    """Load configuration from multiple sources with proper precedence.
    
    Priority order:
    1. CLI arguments (highest priority)
    2. Environment variables
    3. Configuration file
    4. Defaults (lowest priority)
    """
    
    # Start with defaults
    config = ServerConfig()
    
    # Load from file if specified
    if config_file:
        try:
            file_config = ServerConfig.from_file(config_file)
            # Merge file config with defaults
            for key, value in file_config.to_dict().items():
                if key != "custom_config_path":
                    setattr(config, key, value)
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            raise
    
    # Override with environment variables
    try:
        env_config = ServerConfig.from_env()
        for key, value in env_config.to_dict().items():
            if value is not None and value != getattr(ServerConfig(), key):
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