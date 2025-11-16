#!/usr/bin/env python3
# examples/stdio_client_example.py
"""
Fixed Example client for the Chuk MCP Math Server using stdio transport.

This version handles server startup correctly and includes fallback options.
"""

import asyncio
import json
from typing import Dict, Any
from pathlib import Path


class MCPMathClient:
    """Client for communicating with the MCP Math Server via stdio."""

    def __init__(self, server_command: list = None):
        # Use the installed CLI command
        self.server_command = server_command or [
            "chuk-mcp-math-server",
            "--transport",
            "stdio",
        ]
        self.process = None
        self.message_id = 0
        print(f"🔍 Using server command: {' '.join(self.server_command)}")

    async def start(self):
        """Start the server process with better error handling."""
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait a moment for server to start
            await asyncio.sleep(1.0)

            # Check if process started successfully
            if self.process.returncode is not None:
                stderr_data = await self.process.stderr.read()
                error_msg = stderr_data.decode() if stderr_data else "Unknown error"
                raise RuntimeError(f"Server failed to start: {error_msg}")

            print("🚀 Started MCP Math Server")

        except FileNotFoundError:
            raise RuntimeError(
                "Server not found. Please ensure the server is properly installed."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start server: {e}")

    async def stop(self):
        """Stop the server process gracefully."""
        if self.process:
            try:
                # Try graceful termination first
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Force kill if needed
                    self.process.kill()
                    await self.process.wait()
            except Exception as e:
                print(f"⚠️ Error stopping server: {e}")

            print("🛑 Stopped MCP Math Server")

    def _next_id(self) -> int:
        """Get next message ID."""
        self.message_id += 1
        return self.message_id

    async def send_message(
        self, method: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send a message to the server and return the response."""
        if not self.process:
            raise RuntimeError("Server not started")

        message = {"jsonrpc": "2.0", "id": self._next_id(), "method": method}

        if params:
            message["params"] = params

        # Send message
        message_json = json.dumps(message) + "\n"
        self.process.stdin.write(message_json.encode())
        await self.process.stdin.drain()

        # Read response with timeout - handle large responses
        try:
            response_data = b""
            while True:
                chunk = await asyncio.wait_for(
                    self.process.stdout.read(4096), timeout=10.0
                )
                if not chunk:
                    break
                response_data += chunk
                if b"\n" in response_data:
                    # Extract first complete line
                    response_data = response_data.split(b"\n", 1)[0]
                    break
        except asyncio.TimeoutError:
            raise RuntimeError("Server response timeout")

        if not response_data:
            # Check if process died
            if self.process.returncode is not None:
                stderr_data = await self.process.stderr.read()
                error_msg = (
                    stderr_data.decode() if stderr_data else "Process terminated"
                )
                raise RuntimeError(f"Server died: {error_msg}")
            else:
                raise RuntimeError("No response from server")

        try:
            response = json.loads(response_data.decode().strip())
            return response
        except json.JSONDecodeError as e:
            print(f"Raw response: {response_data.decode()[:200]}...")
            raise RuntimeError(f"Invalid JSON response: {e}")

    async def initialize(self):
        """Initialize the connection."""
        response = await self.send_message(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "clientInfo": {"name": "math-client-example", "version": "1.0.0"},
            },
        )

        if response.get("error") is not None:
            raise RuntimeError(f"Initialization failed: {response['error']}")

        # Send initialized notification (no response expected)
        init_msg = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        init_json = json.dumps(init_msg) + "\n"
        self.process.stdin.write(init_json.encode())
        await self.process.stdin.drain()

        print("✅ Initialized connection")
        return response["result"]

    async def list_tools(self) -> list:
        """List available mathematical tools."""
        response = await self.send_message("tools/list")
        if response.get("error") is not None:
            raise RuntimeError(f"Failed to list tools: {response['error']}")

        return response["result"]["tools"]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a mathematical tool."""
        response = await self.send_message(
            "tools/call", {"name": name, "arguments": arguments}
        )

        if response.get("error") is not None:
            raise RuntimeError(f"Tool call failed: {response['error']}")

        return response["result"]


async def demonstrate_number_theory():
    """Demonstrate number theory functions."""
    print("\n🔢 Number Theory Demonstrations")
    print("=" * 50)

    client = MCPMathClient()

    try:
        await client.start()
        await client.initialize()

        # Test if we can list tools first
        try:
            tools = await client.list_tools()
            print(f"📋 Available tools: {len(tools)} found")

            # Show first few tools
            for tool in tools[:5]:
                print(
                    f"   • {tool['name']}: {tool.get('description', 'No description')[:60]}..."
                )
            if len(tools) > 5:
                print(f"   ... and {len(tools) - 5} more tools")

        except Exception as e:
            print(f"❌ Failed to list tools: {e}")
            return

        # Prime operations
        print("\n📊 Prime Operations:")

        # Test primality
        for n in [17, 25, 97]:
            try:
                result = await client.call_tool("is_prime", {"n": n})
                # Extract result from MCP response
                if isinstance(result, dict) and "content" in result:
                    content = result["content"][0]["text"]
                    print(f"  is_prime({n}) = {content}")
                else:
                    print(f"  is_prime({n}) = {result}")
            except Exception as e:
                print(f"  is_prime({n}) failed: {e}")

        # Find next prime
        try:
            result = await client.call_tool("next_prime", {"n": 100})
            if isinstance(result, dict) and "content" in result:
                content = result["content"][0]["text"]
                print(f"  next_prime(100) = {content}")
            else:
                print(f"  next_prime(100) = {result}")
        except Exception as e:
            print(f"  next_prime(100) failed: {e}")

        # Prime factorization
        try:
            result = await client.call_tool("prime_factors", {"n": 60})
            if isinstance(result, dict) and "content" in result:
                content = result["content"][0]["text"]
                print(f"  prime_factors(60) = {content}")
            else:
                print(f"  prime_factors(60) = {result}")
        except Exception as e:
            print(f"  prime_factors(60) failed: {e}")

        # Try a few more functions if available
        basic_functions = [
            ("gcd", {"a": 48, "b": 18}),
            ("lcm", {"a": 12, "b": 18}),
            ("fibonacci", {"n": 10}),
        ]

        print("\n🔐 Additional Operations:")
        for func_name, args in basic_functions:
            try:
                result = await client.call_tool(func_name, args)
                if isinstance(result, dict) and "content" in result:
                    content = result["content"][0]["text"]
                    print(f"  {func_name}({args}) = {content}")
                else:
                    print(f"  {func_name}({args}) = {result}")
            except Exception as e:
                print(f"  {func_name}({args}) failed: {e}")

    except Exception as e:
        print(f"❌ Number theory demonstration failed: {e}")
    finally:
        await client.stop()


async def demonstrate_arithmetic():
    """Demonstrate arithmetic functions."""
    print("\n🧮 Arithmetic Demonstrations")
    print("=" * 50)

    client = MCPMathClient()

    try:
        await client.start()
        await client.initialize()

        # Basic operations
        print("\n📊 Basic Operations:")

        operations = [
            ("add", {"a": 15, "b": 27}),
            ("multiply", {"a": 6, "b": 7}),
            ("power", {"base": 2, "exponent": 10}),
            ("sqrt", {"x": 144}),
        ]

        for op_name, args in operations:
            try:
                result = await client.call_tool(op_name, args)
                if isinstance(result, dict) and "content" in result:
                    content = result["content"][0]["text"]
                    print(f"  {op_name}({args}) = {content}")
                else:
                    print(f"  {op_name}({args}) = {result}")
            except Exception as e:
                print(f"  {op_name}({args}) failed: {e}")

    except Exception as e:
        print(f"❌ Arithmetic demonstration failed: {e}")
    finally:
        await client.stop()


async def test_server_connectivity():
    """Test basic server connectivity and capabilities."""
    print("\n🔍 Testing Server Connectivity")
    print("=" * 40)

    client = MCPMathClient()

    try:
        print("🚀 Starting server...")
        await client.start()

        print("🔗 Initializing connection...")
        init_result = await client.initialize()

        print("✅ Server connected successfully!")
        print(f"📋 Server info: {init_result.get('serverInfo', {})}")

        # Test tool listing
        tools = await client.list_tools()
        print(f"🛠️ Available tools: {len(tools)}")

        # Test a simple operation
        try:
            result = await client.call_tool("add", {"a": 2, "b": 3})
            print(f"🧮 Test calculation: add(2, 3) = {result}")
            print("✅ Server is fully functional!")
            return True

        except Exception as e:
            print(f"⚠️ Tool execution failed: {e}")
            return False

    except Exception as e:
        print(f"❌ Server connectivity test failed: {e}")
        print("💡 This might be due to:")
        print("   - Server not installed properly")
        print("   - Missing dependencies")
        print("   - Configuration issues")
        return False
    finally:
        await client.stop()


async def main():
    """Main demonstration function with robust error handling."""
    print("🧮 Chuk MCP Math Server - Client Examples")
    print("=" * 60)

    # First test basic connectivity
    server_works = await test_server_connectivity()

    if server_works:
        print("\n🎯 Running full demonstrations with live server...")
        await demonstrate_number_theory()
        await demonstrate_arithmetic()
        print("\n✅ All demonstrations completed!")
    else:
        print("\n❌ Server unavailable - check installation and dependencies")
        print("\n💡 To fix this:")
        print("   1. Ensure chuk-mcp-math-server is properly installed")
        print("   2. Install dependencies: pip install chuk-mcp-math chuk-mcp")
        print("   3. Check server location in src/chuk_mcp_math_server/")


if __name__ == "__main__":
    asyncio.run(main())
