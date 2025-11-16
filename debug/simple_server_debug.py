#!/usr/bin/env python3
# debug/simple_server_debug.py
"""
Simple test to verify the math server works.
"""

import asyncio
import sys
import json
from pathlib import Path


async def simple_server_test():
    """Run a simple test of the math server."""
    print("🧪 Simple Math Server Test")
    print("=" * 30)

    # Use the installed CLI command
    server_cmd = ["chuk-mcp-math-server", "--transport", "stdio"]
    print("📍 Using installed command: chuk-mcp-math-server")

    try:
        # Start server
        print("🚀 Starting server...")
        process = await asyncio.create_subprocess_exec(
            *server_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
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
                "clientInfo": {"name": "test-client"},
            },
        }

        # Send message
        msg_json = json.dumps(init_msg) + "\n"
        process.stdin.write(msg_json.encode())
        await process.stdin.drain()

        # Read response - use read until newline for large responses
        response_data = b""
        while True:
            chunk = await asyncio.wait_for(process.stdout.read(1024), timeout=10.0)
            if not chunk:
                break
            response_data += chunk
            if b"\n" in response_data:
                break

        response = json.loads(response_data.decode().strip())

        if response.get("error") is not None:
            print(f"❌ Initialize failed: {response['error']}")
            return False

        print("✅ Initialize successful")

        # Test a simple calculation (skip tools/list as it's too large)
        calc_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "add", "arguments": {"a": 5, "b": 3}},
        }

        msg_json = json.dumps(calc_msg) + "\n"
        process.stdin.write(msg_json.encode())
        await process.stdin.drain()

        # Read response
        response_data = b""
        while True:
            chunk = await asyncio.wait_for(process.stdout.read(1024), timeout=10.0)
            if not chunk:
                break
            response_data += chunk
            if b"\n" in response_data:
                break

        response = json.loads(response_data.decode().strip())

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
        if "process" in locals():
            process.terminate()
            await process.wait()
        return False


if __name__ == "__main__":
    success = asyncio.run(simple_server_test())
    sys.exit(0 if success else 1)
