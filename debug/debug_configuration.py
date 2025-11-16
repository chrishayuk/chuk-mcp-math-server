#!/usr/bin/env python3
# debug/debug_configuration.py
"""
Test the configuration system with different setups.
"""

import asyncio
import subprocess
import json
import tempfile
import os
from pathlib import Path


async def test_configuration_system():
    """Test various configuration options."""
    print("⚙️ Configuration System Test")
    print("=" * 40)

    # Use the installed CLI command
    server_base_cmd = ["chuk-mcp-math-server"]
    print("📍 Using installed command: chuk-mcp-math-server")

    # Test 1: Show current configuration
    print("\n🔍 Test 1: Show Configuration")
    try:
        result = subprocess.run(
            [*server_base_cmd, "--show-config"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ Configuration display works")
            config = json.loads(result.stdout.split("\n", 1)[1])
            print(
                f"📊 Default functions enabled: {config.get('enable_tools', 'unknown')}"
            )
        else:
            print(f"❌ Config display failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Config test failed: {e}")

    # Test 2: Domain filtering
    print("\n🔍 Test 2: Domain Filtering")
    try:
        result = subprocess.run(
            [*server_base_cmd, "--domains", "arithmetic", "--show-config"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ Domain filtering works")
            config = json.loads(result.stdout.split("\n", 1)[1])
            print(f"📊 Domain allowlist: {config.get('domain_allowlist', [])}")
        else:
            print(f"❌ Domain filtering failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Domain test failed: {e}")

    # Test 3: Configuration file
    print("\n🔍 Test 3: Configuration File")

    config_content = """
transport: "stdio"
enable_tools: true
enable_prompts: false
enable_resources: false
domain_allowlist:
  - "arithmetic"
function_allowlist:
  - "add"
  - "subtract"
  - "multiply"
cache_strategy: "none"
computation_timeout: 5.0
"""

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_file = f.name

        result = subprocess.run(
            [*server_base_cmd, "--config", config_file, "--show-config"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        os.unlink(config_file)

        if result.returncode == 0:
            print("✅ Configuration file loading works")
            config = json.loads(result.stdout.split("\n", 1)[1])
            print(f"📊 Function allowlist: {config.get('function_allowlist', [])}")
        else:
            print(f"❌ Config file test failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Config file test failed: {e}")

    # Test 4: Environment variables
    print("\n🔍 Test 4: Environment Variables")
    try:
        env = os.environ.copy()
        env.update(
            {
                "MCP_MATH_ENABLE_PROMPTS": "false",
                "MCP_MATH_CACHE_STRATEGY": "memory",
                "MCP_MATH_DOMAIN_ALLOWLIST": "arithmetic,number_theory",
            }
        )

        result = subprocess.run(
            [*server_base_cmd, "--show-config"],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )

        if result.returncode == 0:
            print("✅ Environment variables work")
            config = json.loads(result.stdout.split("\n", 1)[1])
            print(f"📊 Cache strategy: {config.get('cache_strategy', 'unknown')}")
        else:
            print(f"❌ Environment test failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Environment test failed: {e}")

    print("\n✅ Configuration tests completed!")


if __name__ == "__main__":
    asyncio.run(test_configuration_system())
