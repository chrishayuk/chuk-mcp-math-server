#!/usr/bin/env python3
# debug/debug_protocol_handler.py
"""
Debug script to check what methods are available on the protocol_handler.
"""

import sys
import inspect

try:
    from chuk_mcp.server import MCPServer
    from chuk_mcp.protocol.types import ServerCapabilities

    print("🔍 Inspecting protocol_handler:")
    print("=" * 50)

    # Create a server instance
    server = MCPServer(name="test", version="1.0.0")
    handler = server.protocol_handler

    print(f"📋 Protocol handler type: {type(handler)}")

    # Get all methods and attributes
    methods = []
    attributes = []

    for name in dir(handler):
        if not name.startswith("_"):
            obj = getattr(handler, name)
            if callable(obj):
                methods.append(name)
            else:
                attributes.append(name)

    print("📋 Available Methods:")
    for method in sorted(methods):
        try:
            sig = inspect.signature(getattr(handler, method))
            print(f"  • {method}{sig}")
        except:
            print(f"  • {method}()")

    print("\n📋 Available Attributes:")
    for attr in sorted(attributes):
        print(f"  • {attr}")

    # Check for specific methods we need
    required_methods = [
        "run_stdio",
        "run",
        "start",
        "serve",
        "handle_stdio",
        "handle_message",
    ]

    print("\n🔍 Checking for required methods:")
    for method in required_methods:
        if hasattr(handler, method):
            print(f"  ✅ {method} - Available")
        else:
            print(f"  ❌ {method} - Missing")

    # Check the handler's class hierarchy
    print("\n🏗️ Class hierarchy:")
    for cls in handler.__class__.__mro__:
        print(f"  • {cls}")

    # Check if there are any run-like methods
    print("\n🏃 Run-like methods:")
    for method in methods:
        if any(
            keyword in method.lower()
            for keyword in ["run", "start", "serve", "handle", "process", "execute"]
        ):
            print(f"  • {method}")

    # Check what's available in the chuk_mcp module
    print("\n📦 Checking chuk_mcp module structure:")
    try:
        import chuk_mcp

        print(f"  • chuk_mcp version: {getattr(chuk_mcp, '__version__', 'unknown')}")

        # Check submodules
        for attr in dir(chuk_mcp):
            if not attr.startswith("_"):
                obj = getattr(chuk_mcp, attr)
                if hasattr(obj, "__file__") or hasattr(obj, "__path__"):
                    print(f"  • {attr} (module)")
                else:
                    print(f"  • {attr}: {type(obj)}")
    except Exception as e:
        print(f"  ❌ Error checking chuk_mcp: {e}")

except ImportError as e:
    print(f"❌ Failed to import chuk_mcp: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error inspecting protocol handler: {e}")
    sys.exit(1)
