#!/usr/bin/env python3
# src/chuk_mcp_math_server/__init__.py
"""
Chuk MCP Math Server Package

A highly configurable Mathematical Computation Protocol (MCP) server that provides
comprehensive mathematical functions with flexible transport options (stdio/HTTP).
"""

__version__ = "0.2.0"
__author__ = "Chuk AI Team"
__description__ = "Configurable mathematical computation server for MCP protocol"

# Main exports
from .cli import main
from .config import ServerConfig, load_configuration_from_sources
from .function_filter import FunctionFilter
from .math_config import MathServerConfig, load_math_configuration_from_sources
from .math_server import ConfigurableMCPMathServer, create_math_server

__all__ = [
    # Core classes
    "ConfigurableMCPMathServer",
    "ServerConfig",
    "MathServerConfig",
    "FunctionFilter",
    # Factory functions
    "create_math_server",
    "load_configuration_from_sources",
    "load_math_configuration_from_sources",
    # CLI
    "main",
    # Metadata
    "__version__",
    "__author__",
    "__description__",
]


# Convenience functions for quick server startup
def run_server_stdio(**kwargs):
    """Quick stdio server startup."""
    server = create_math_server(transport="stdio", **kwargs)
    server.run()


def run_server_http(port=8000, host="0.0.0.0", **kwargs):
    """Quick HTTP server startup."""
    server = create_math_server(transport="http", port=port, host=host, **kwargs)
    server.run()
