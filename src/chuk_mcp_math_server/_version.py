#!/usr/bin/env python3
# src/chuk_mcp_math_server/_version.py
"""
Version management utilities for chuk-mcp-math-server.

This module provides robust version detection that works in development,
installed packages, and various deployment scenarios.
"""

import sys
from pathlib import Path
from typing import Optional

__all__ = ["get_version", "VERSION", "__version__"]

def get_version() -> str:
    """
    Get the package version using multiple fallback strategies.
    
    Priority order:
    1. Installed package metadata (importlib.metadata or pkg_resources)
    2. Parse pyproject.toml directly
    3. Environment variable
    4. Hardcoded fallback
    
    Returns:
        Version string (e.g., "0.1.0")
    """
    
    # Strategy 1: Try installed package metadata
    version = _get_version_from_metadata()
    if version:
        return version
    
    # Strategy 2: Parse pyproject.toml directly
    version = _get_version_from_pyproject()
    if version:
        return version
    
    # Strategy 3: Environment variable
    version = _get_version_from_env()
    if version:
        return version
    
    # Strategy 4: Hardcoded fallback
    return "0.1.0"

def _get_version_from_metadata() -> Optional[str]:
    """Try to get version from installed package metadata."""
    
    # Try importlib.metadata (Python 3.8+)
    try:
        if sys.version_info >= (3, 8):
            from importlib.metadata import version, PackageNotFoundError
        else:
            from importlib_metadata import version, PackageNotFoundError
        
        return version("chuk-mcp-math-server")
    
    except (ImportError, PackageNotFoundError):
        pass
    
    # Try pkg_resources (older method)
    try:
        import pkg_resources
        return pkg_resources.get_distribution("chuk-mcp-math-server").version
    except Exception:
        pass
    
    return None

def _get_version_from_pyproject() -> Optional[str]:
    """Try to parse version from pyproject.toml."""
    
    # Find pyproject.toml - check multiple locations
    possible_paths = [
        Path(__file__).parent.parent.parent / "pyproject.toml",  # Development
        Path(__file__).parent.parent / "pyproject.toml",        # Alternative
        Path.cwd() / "pyproject.toml",                          # Current directory
    ]
    
    pyproject_path = None
    for path in possible_paths:
        if path.exists():
            pyproject_path = path
            break
    
    if not pyproject_path:
        return None
    
    # Try tomllib (Python 3.11+)
    try:
        import tomllib
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            return data.get("project", {}).get("version")
    except ImportError:
        pass
    
    # Try tomli (backport)
    try:
        import tomli
        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)
            return data.get("project", {}).get("version")
    except ImportError:
        pass
    
    # Fallback: manual parsing with regex
    try:
        import re
        content = pyproject_path.read_text(encoding="utf-8")
        
        # Look for version = "x.y.z" in [project] section
        project_section = False
        for line in content.split('\n'):
            line = line.strip()
            
            if line == '[project]':
                project_section = True
                continue
            elif line.startswith('[') and line != '[project]':
                project_section = False
                continue
            
            if project_section and line.startswith('version'):
                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', line)
                if match:
                    return match.group(1)
    
    except Exception:
        pass
    
    return None

def _get_version_from_env() -> Optional[str]:
    """Try to get version from environment variable."""
    import os
    return os.environ.get("CHUK_MCP_MATH_SERVER_VERSION")

def get_version_info() -> dict:
    """Get detailed version information for debugging."""
    info = {
        "version": get_version(),
        "python_version": sys.version,
        "detection_method": None,
        "available_methods": []
    }
    
    # Test each method
    methods = [
        ("metadata", _get_version_from_metadata),
        ("pyproject", _get_version_from_pyproject), 
        ("environment", _get_version_from_env)
    ]
    
    for name, method in methods:
        try:
            result = method()
            if result:
                info["available_methods"].append(name)
                if info["detection_method"] is None:
                    info["detection_method"] = name
        except Exception as e:
            info[f"{name}_error"] = str(e)
    
    return info

# Module-level version constants
VERSION = get_version()
__version__ = VERSION

def print_version_info():
    """Print detailed version information for debugging."""
    info = get_version_info()
    
    print(f"📦 chuk-mcp-math-server version: {info['version']}")
    print(f"🐍 Python version: {info['python_version']}")
    print(f"🔍 Detection method: {info['detection_method']}")
    print(f"✅ Available methods: {', '.join(info['available_methods'])}")
    
    # Show any errors
    error_keys = [k for k in info.keys() if k.endswith('_error')]
    if error_keys:
        print("⚠️ Method errors:")
        for key in error_keys:
            method = key.replace('_error', '')
            print(f"   {method}: {info[key]}")

if __name__ == "__main__":
    print_version_info()