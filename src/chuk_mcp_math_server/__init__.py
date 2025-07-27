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
from .math_server import (
    ConfigurableMCPMathServer,
    ServerConfig,
    FunctionFilter,
    main
)

# Configuration helpers
from .math_server import load_configuration

# Version utilities
from ._version import get_version, get_version_info, print_version_info

__all__ = [
    "ConfigurableMCPMathServer",
    "ServerConfig", 
    "FunctionFilter",
    "main",
    "load_configuration",
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
        "chuk-mcp>=0.5",
        "chuk-mcp-math>=0.1.0",
        "fastapi>=0.116.1",
        "httpx>=0.28.1",
        "pyyaml>=6.0.2",
        "uvicorn>=0.35.0"
    ],
    "optional_dependencies": {
        "dev": ["pytest", "pytest-asyncio", "black", "isort", "flake8", "mypy", "pre-commit"]
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
    
    try:
        import fastapi
        dependencies["required"]["fastapi"] = True
    except ImportError:
        dependencies["required"]["fastapi"] = False
    
    try:
        import uvicorn
        dependencies["required"]["uvicorn"] = True
    except ImportError:
        dependencies["required"]["uvicorn"] = False
    
    try:
        import httpx
        dependencies["required"]["httpx"] = True
    except ImportError:
        dependencies["required"]["httpx"] = False
    
    try:
        import yaml
        dependencies["required"]["pyyaml"] = True
    except ImportError:
        dependencies["required"]["pyyaml"] = False
    
    # Check optional dependencies
    try:
        import pytest
        dependencies["optional"]["pytest"] = True
    except ImportError:
        dependencies["optional"]["pytest"] = False
    
    try:
        import black
        dependencies["optional"]["black"] = True
    except ImportError:
        dependencies["optional"]["black"] = False
    
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
            "pytest": "Testing framework",
            "black": "Code formatting"
        }.get(dep, dep)
        print(f"  {status} {dep} ({feature})")
    
    # Installation suggestions
    missing_required = [dep for dep, available in deps["required"].items() if not available]
    missing_optional = [dep for dep, available in deps["optional"].items() if not available]
    
    if missing_required:
        print("\n❌ Missing required dependencies:")
        for dep in missing_required:
            print(f"   pip install {dep}")
    
    if missing_optional:
        print("\n💡 To install missing optional dependencies:")
        print("   pip install chuk-mcp-math-server[dev]  # Install all dev deps")

# Convenience function for quick server startup
def create_server(config_file=None, **kwargs):
    """Create a configured server instance.
    
    Args:
        config_file: Optional path to configuration file
        **kwargs: Additional configuration options
    
    Returns:
        ConfigurableMCPMathServer instance
    """
    if config_file:
        config = ServerConfig.from_file(config_file)
        # Apply any overrides
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
    else:
        config = ServerConfig(**kwargs)
    
    return ConfigurableMCPMathServer(config)

def run_server_stdio(**kwargs):
    """Quick stdio server startup."""
    import asyncio
    server = create_server(transport="stdio", **kwargs)
    asyncio.run(server.run())

def run_server_http(port=8000, host="0.0.0.0", **kwargs):
    """Quick HTTP server startup."""
    import asyncio
    server = create_server(transport="http", port=port, host=host, **kwargs)
    asyncio.run(server.run())