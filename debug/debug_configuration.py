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
    
    # Find server in the correct location
    current_dir = Path(__file__).parent
    server_paths = [
        current_dir.parent / "src" / "chuk_mcp_math_server" / "math_server.py",
        "src/chuk_mcp_math_server/math_server.py",
        Path(__file__).parent.parent / "src" / "chuk_mcp_math_server" / "math_server.py"
    ]
    
    server_path = None
    for path in server_paths:
        if Path(path).exists():
            server_path = str(path)
            break
    
    if not server_path:
        # Fallback to module execution
        server_base_cmd = ["python", "-m", "chuk_mcp_math_server.math_server"]
        print("📍 Using module execution: python -m chuk_mcp_math_server.math_server")
    else:
        server_base_cmd = ["python", server_path]
        print(f"📍 Found server at: {server_path}")
    
    # Test 1: Show current configuration
    print("\n🔍 Test 1: Show Configuration")
    try:
        result = subprocess.run([
            *server_base_cmd, "--show-config"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Configuration display works")
            config = json.loads(result.stdout.split('\n', 1)[1])
            print(f"📊 Default functions enabled: {config.get('enable_tools', 'unknown')}")
        else:
            print(f"❌ Config display failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Config test failed: {e}")
    
    # Test 2: Domain filtering
    print("\n🔍 Test 2: Domain Filtering")
    try:
        result = subprocess.run([
            *server_base_cmd,
            "--domains", "arithmetic",
            "--show-config"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Domain filtering works")
            config = json.loads(result.stdout.split('\n', 1)[1])
            print(f"📊 Domain whitelist: {config.get('domain_whitelist', [])}")
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
domain_whitelist:
  - "arithmetic"
function_whitelist:
  - "add"
  - "subtract"
  - "multiply"
cache_strategy: "none"
computation_timeout: 5.0
"""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        result = subprocess.run([
            *server_base_cmd,
            "--config", config_file,
            "--show-config"
        ], capture_output=True, text=True, timeout=10)
        
        os.unlink(config_file)
        
        if result.returncode == 0:
            print("✅ Configuration file loading works")
            config = json.loads(result.stdout.split('\n', 1)[1])
            print(f"📊 Function whitelist: {config.get('function_whitelist', [])}")
        else:
            print(f"❌ Config file test failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Config file test failed: {e}")
    
    # Test 4: Environment variables
    print("\n🔍 Test 4: Environment Variables")
    try:
        env = os.environ.copy()
        env.update({
            'MCP_MATH_ENABLE_PROMPTS': 'false',
            'MCP_MATH_CACHE_STRATEGY': 'memory',
            'MCP_MATH_DOMAIN_WHITELIST': 'arithmetic,number_theory'
        })
        
        result = subprocess.run([
            *server_base_cmd, "--show-config"
        ], capture_output=True, text=True, timeout=10, env=env)
        
        if result.returncode == 0:
            print("✅ Environment variables work")
            config = json.loads(result.stdout.split('\n', 1)[1])
            print(f"📊 Cache strategy: {config.get('cache_strategy', 'unknown')}")
        else:
            print(f"❌ Environment test failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
    
    print("\n✅ Configuration tests completed!")

if __name__ == "__main__":
    asyncio.run(test_configuration_system())