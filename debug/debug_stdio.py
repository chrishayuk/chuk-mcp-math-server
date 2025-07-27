#!/usr/bin/env python3
# debug/debug_stdio.py
"""
Simple test to verify the math server works.
"""

import asyncio
import subprocess
import sys
import json
from pathlib import Path

async def simple_server_test():
    """Run a simple test of the math server."""
    print("🧪 Simple Math Server Test")
    print("=" * 30)
    
    # Try to find the server in the correct location
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
    
    # Fallback to module execution
    if not server_path:
        server_cmd = ["python", "-m", "chuk_mcp_math_server.math_server", "--transport", "stdio"]
        print("📍 Using module execution: python -m chuk_mcp_math_server.math_server")
    else:
        server_cmd = ["python", server_path, "--transport", "stdio"]
        print(f"📍 Found server at: {server_path}")
    
    try:
        # Start server
        print("🚀 Starting server...")
        process = await asyncio.create_subprocess_exec(
            *server_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for startup
        await asyncio.sleep(2)
        
        # Check if running
        if process.returncode is not None:
            stderr = await process.stderr.read()
            print(f"❌ Server failed to start: {stderr.decode()}")
            return False
        
        print("✅ Server started successfully")
        
        # Test initialize
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "clientInfo": {"name": "test-client"}
            }
        }
        
        # Send message
        msg_json = json.dumps(init_msg) + "\n"
        process.stdin.write(msg_json.encode())
        await process.stdin.drain()
        
        # Read response
        response_line = await asyncio.wait_for(
            process.stdout.readline(), 
            timeout=10.0
        )
        
        response = json.loads(response_line.decode())
        
        if response.get("error") is not None:
            print(f"❌ Initialize failed: {response['error']}")
            return False
        
        print("✅ Initialize successful")
        
        # Test tool list
        tools_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        msg_json = json.dumps(tools_msg) + "\n"
        process.stdin.write(msg_json.encode())
        await process.stdin.drain()
        
        response_line = await asyncio.wait_for(
            process.stdout.readline(),
            timeout=10.0
        )
        
        response = json.loads(response_line.decode())
        
        if response.get("error") is not None:
            print(f"❌ Tools list failed: {response['error']}")
            return False
        
        tools = response["result"]["tools"]
        print(f"✅ Found {len(tools)} mathematical tools")
        
        # Test a simple calculation
        calc_msg = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "add",
                "arguments": {"a": 5, "b": 3}
            }
        }
        
        msg_json = json.dumps(calc_msg) + "\n"
        process.stdin.write(msg_json.encode())
        await process.stdin.drain()
        
        response_line = await asyncio.wait_for(
            process.stdout.readline(),
            timeout=10.0
        )
        
        response = json.loads(response_line.decode())
        
        if response.get("error") is not None:
            print(f"❌ Calculation failed: {response['error']}")
            return False
        
        print("✅ Mathematical calculation successful")
        print(f"📊 add(5, 3) = {response['result']}")
        
        # Clean shutdown
        process.terminate()
        await process.wait()
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if 'process' in locals():
            process.terminate()
            await process.wait()
        return False

if __name__ == "__main__":
    success = asyncio.run(simple_server_test())
    sys.exit(0 if success else 1)