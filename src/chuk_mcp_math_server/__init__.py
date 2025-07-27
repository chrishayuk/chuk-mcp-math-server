#!/usr/bin/env python3
# src/chuk_mcp_math_server/__init__.py
"""
Chuk MCP Math Server Package

A highly configurable Mathematical Computation Protocol (MCP) server that provides
comprehensive mathematical functions with flexible transport options (stdio/HTTP).
"""

# Import version dynamically
from ._version import get_version, __version__

__author__ = "Chuk MCP Team"
__description__ = "Configurable mathematical computation server for MCP protocol"

# Main exports
from .config import ServerConfig, load_configuration_from_sources
from .math_config import MathServerConfig, load_math_configuration_from_sources
from .function_filter import FunctionFilter
from .base_server import BaseMCPServer
from .math_server import ConfigurableMCPMathServer, create_math_server
from .cli import main

# Version utilities
from ._version import get_version, get_version_info, print_version_info

__all__ = [
    # Core classes
    "ConfigurableMCPMathServer",
    "BaseMCPServer",
    "ServerConfig", 
    "MathServerConfig",
    "FunctionFilter",
    
    # Factory functions
    "create_math_server",
    "load_configuration_from_sources",
    "load_math_configuration_from_sources",
    
    # CLI
    "main",
    
    # Version utilities
    "get_version",
    "get_version_info", 
    "print_version_info",
    "__version__",
    "__author__",
    "__description__"
]

# Package metadata
PACKAGE_INFO = {
    "name": "chuk-mcp-math-server",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "supports_stdio": True,
    "supports_http": True,
    "supported_transports": ["stdio", "http"],
    "default_transport": "stdio",
    "required_dependencies": [
        "chuk-mcp",
        "chuk-mcp-math"
    ],
    "optional_dependencies": {
        "http": ["fastapi", "uvicorn"],
        "yaml": ["pyyaml"],
        "full": ["fastapi", "uvicorn", "pyyaml", "httpx"]
    }
}

def get_package_info():
    """Get package information."""
    info = PACKAGE_INFO.copy()
    info["version"] = __version__  # Use dynamic version
    return info

def check_dependencies():
    """Check which optional dependencies are available."""
    dependencies = {
        "required": {},
        "optional": {}
    }
    
    # Check required dependencies
    try:
        import chuk_mcp
        dependencies["required"]["chuk_mcp"] = True
    except ImportError:
        dependencies["required"]["chuk_mcp"] = False
    
    try:
        import chuk_mcp_math
        dependencies["required"]["chuk_mcp_math"] = True
    except ImportError:
        dependencies["required"]["chuk_mcp_math"] = False
    
    # Check optional dependencies
    try:
        import fastapi
        import uvicorn
        dependencies["optional"]["http"] = True
    except ImportError:
        dependencies["optional"]["http"] = False
    
    try:
        import yaml
        dependencies["optional"]["yaml"] = True
    except ImportError:
        dependencies["optional"]["yaml"] = False
    
    try:
        import httpx
        dependencies["optional"]["httpx"] = True
    except ImportError:
        dependencies["optional"]["httpx"] = False
    
    return dependencies

def print_dependency_status():
    """Print current dependency status."""
    deps = check_dependencies()
    
    print(f"📦 {PACKAGE_INFO['name']} v{__version__}")
    print("=" * 50)
    
    print("\n✅ Required Dependencies:")
    for dep, available in deps["required"].items():
        status = "✅" if available else "❌"
        print(f"  {status} {dep}")
    
    print("\n🔧 Optional Dependencies:")
    for dep, available in deps["optional"].items():
        status = "✅" if available else "❌"
        feature = {
            "http": "HTTP transport support",
            "yaml": "YAML configuration files", 
            "httpx": "HTTP client examples"
        }.get(dep, dep)
        print(f"  {status} {dep} ({feature})")
    
    # Installation suggestions
    missing_optional = [dep for dep, available in deps["optional"].items() if not available]
    if missing_optional:
        print("\n💡 To install missing optional dependencies:")
        if "http" in missing_optional:
            print("   pip install fastapi uvicorn  # For HTTP transport")
        if "yaml" in missing_optional:
            print("   pip install pyyaml  # For YAML config files")
        if "httpx" in missing_optional:
            print("   pip install httpx  # For HTTP client examples")
        print("   pip install fastapi uvicorn pyyaml httpx  # Install all optional deps")

# Convenience functions for quick server startup
def run_server_stdio(**kwargs):
    """Quick stdio server startup."""
    import asyncio
    server = create_math_server(transport="stdio", **kwargs)
    asyncio.run(server.run())

def run_server_http(port=8000, host="0.0.0.0", **kwargs):
    """Quick HTTP server startup."""
    import asyncio
    server = create_math_server(transport="http", port=port, host=host, **kwargs)
    asyncio.run(server.run())