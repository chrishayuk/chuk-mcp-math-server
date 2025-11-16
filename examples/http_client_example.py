#!/usr/bin/env python3
# examples/http_client_example.py
"""
HTTP client example for the Chuk MCP Math Server using HTTP streamable transport.

This demonstrates the HTTP/SSE capabilities of the server with streaming support.
"""

import asyncio
import json
import subprocess
from typing import Dict, Any
from pathlib import Path

# HTTP client requirements
try:
    import httpx
    import asyncio

    _http_available = True
except ImportError:
    _http_available = False
    print("❌ HTTP client requires httpx: pip install httpx")


class MCPMathHTTPClient:
    """Client for communicating with the MCP Math Server via HTTP transport."""

    def __init__(
        self, base_url: str = "http://localhost:8000", enable_streaming: bool = True
    ):
        self.base_url = base_url
        self.enable_streaming = enable_streaming
        self.session_id = None
        self.message_id = 0
        self.session = None

        if not _http_available:
            raise RuntimeError("httpx required for HTTP client: pip install httpx")

        print(f"🌐 HTTP MCP Client connecting to: {base_url}")
        if enable_streaming:
            print("📡 Streaming support: enabled")
        else:
            print("📄 Streaming support: disabled")

    async def start(self):
        """Start the HTTP session."""
        self.session = httpx.AsyncClient(timeout=30.0)
        print("🚀 Started HTTP session")

    async def stop(self):
        """Stop the HTTP session."""
        if self.session:
            await self.session.aclose()
            print("🛑 Stopped HTTP session")

    def _next_id(self) -> int:
        """Get next message ID."""
        self.message_id += 1
        return self.message_id

    async def send_message(
        self, method: str, params: Dict[str, Any] = None, use_streaming: bool = None
    ) -> Dict[str, Any]:
        """Send a message to the server and return the response."""
        if not self.session:
            raise RuntimeError("Session not started - call start() first")

        message = {"jsonrpc": "2.0", "id": self._next_id(), "method": method}

        if params:
            message["params"] = params

        # Determine if we should use streaming
        if use_streaming is None:
            use_streaming = self.enable_streaming and self._should_stream(
                method, params
            )

        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        if use_streaming:
            headers["Accept"] = "text/event-stream"

        try:
            response = await self.session.post(
                f"{self.base_url}/mcp", json=message, headers=headers
            )

            # Check for session ID in response
            if "mcp-session-id" in response.headers:
                self.session_id = response.headers["mcp-session-id"]

            if use_streaming and "text/event-stream" in response.headers.get(
                "content-type", ""
            ):
                return await self._handle_streaming_response(response)
            else:
                response_data = response.json()
                return response_data

        except httpx.RequestError as e:
            raise RuntimeError(f"HTTP request failed: {e}")
        except httpx.TimeoutException:
            raise RuntimeError("HTTP request timeout")

    def _should_stream(self, method: str, params: Dict[str, Any]) -> bool:
        """Determine if this request should use streaming."""
        if method != "tools/call":
            return False

        if not params:
            return False

        # Stream for computationally intensive functions
        tool_name = params.get("name", "")
        streaming_functions = [
            "fibonacci",
            "prime_factors",
            "next_prime",
            "collatz_sequence",
            "partition_count",
            "continued_fraction_expansion",
            "vampire_numbers",
        ]

        if tool_name in streaming_functions:
            return True

        # Stream for large parameter values
        arguments = params.get("arguments", {})
        if isinstance(arguments, dict):
            for key, value in arguments.items():
                if isinstance(value, int) and value > 1000:
                    return True

        return False

    async def _handle_streaming_response(self, response) -> Dict[str, Any]:
        """Handle Server-Sent Events streaming response."""
        print("📡 Receiving streaming response...")

        final_result = None
        events_received = 0
        event_type = None

        async for line in response.aiter_lines():
            if not line.strip():
                continue

            if line.startswith("event: "):
                event_type = line[7:]
                continue

            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    events_received += 1

                    if event_type == "start":
                        print(f"  📥 Stream started: {data.get('status', 'unknown')}")
                    elif event_type == "progress":
                        status = data.get("status", "unknown")
                        progress = data.get("progress", 0)
                        function = data.get("function", "")
                        print(f"  ⏳ Progress: {status} ({progress}%) {function}")
                    elif event_type == "message":
                        print("  📨 Result received")
                        final_result = data
                    elif event_type == "completion":
                        exec_time = data.get("execution_time", 0)
                        print(
                            f"  ✅ Stream completed in {exec_time:.3f}s ({events_received} events)"
                        )
                    elif event_type == "error":
                        print(f"  ❌ Stream error: {data}")
                        return data
                    elif event_type == "timeout":
                        print(f"  ⏰ Stream timeout: {data}")
                        return {"error": {"code": -32603, "message": "Stream timeout"}}

                except json.JSONDecodeError:
                    continue

        return final_result or {
            "error": {"code": -32603, "message": "No final result in stream"}
        }

    async def initialize(self):
        """Initialize the connection."""
        response = await self.send_message(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "clientInfo": {"name": "math-http-client", "version": "1.0.0"},
            },
            use_streaming=False,
        )

        if response.get("error") is not None:
            raise RuntimeError(f"Initialization failed: {response['error']}")

        print("✅ Initialized HTTP connection")
        return response["result"]

    async def list_tools(self) -> list:
        """List available mathematical tools."""
        response = await self.send_message("tools/list", use_streaming=False)
        if response.get("error") is not None:
            raise RuntimeError(f"Failed to list tools: {response['error']}")

        return response["result"]["tools"]

    async def call_tool(
        self, name: str, arguments: Dict[str, Any], force_streaming: bool = None
    ) -> Any:
        """Call a mathematical tool."""
        response = await self.send_message(
            "tools/call",
            {"name": name, "arguments": arguments},
            use_streaming=force_streaming,
        )

        if response.get("error") is not None:
            raise RuntimeError(f"Tool call failed: {response['error']}")

        return response["result"]

    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information from the root endpoint."""
        try:
            response = await self.session.get(f"{self.base_url}/")
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to get server info: {e}")

    async def get_health(self) -> Dict[str, Any]:
        """Get server health information."""
        try:
            response = await self.session.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to get health info: {e}")


async def start_http_server(port: int = 8000) -> subprocess.Popen:
    """Start the HTTP server and wait for it to be ready."""
    # Use the installed CLI command
    server_cmd = ["chuk-mcp-math-server", "--transport", "http", "--port", str(port)]

    print(f"🚀 Starting HTTP server on port {port}...")
    print(f"📍 Command: {' '.join(server_cmd)}")

    # Start server process
    process = subprocess.Popen(
        server_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Wait for server to be ready
    base_url = f"http://localhost:{port}"
    max_attempts = 30

    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/health", timeout=2.0)
                if response.status_code == 200:
                    print(f"✅ HTTP server ready at {base_url}")
                    return process
        except:
            pass

        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print("❌ Server failed to start:")
            print(f"  stdout: {stdout.decode()}")
            print(f"  stderr: {stderr.decode()}")
            raise RuntimeError("Server process terminated")

        await asyncio.sleep(1)

    process.terminate()
    raise RuntimeError(f"Server not ready after {max_attempts} seconds")


async def demonstrate_http_number_theory():
    """Demonstrate number theory functions via HTTP."""
    print("\n🔢 HTTP Number Theory Demonstrations")
    print("=" * 50)

    client = MCPMathHTTPClient()

    try:
        await client.start()
        await client.initialize()

        # Test server info
        try:
            server_info = await client.get_server_info()
            print(
                f"🌐 Server: {server_info.get('server', 'unknown')} v{server_info.get('version', 'unknown')}"
            )
            # FIX: Read functions_available from the correct field
            print(
                f"📊 Functions available: {server_info.get('functions_available', 0)}"
            )
        except Exception as e:
            print(f"⚠️ Could not get server info: {e}")

        # List tools
        try:
            tools = await client.list_tools()
            print(f"📋 Available tools: {len(tools)} found")

            # Show sample tools
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
        print("\n📊 Prime Operations (with streaming):")

        # Test primality with potential streaming
        for n in [17, 97, 1009]:
            try:
                print(f"\n🔍 Testing is_prime({n})...")
                result = await client.call_tool("is_prime", {"n": n})

                if isinstance(result, dict) and "content" in result:
                    content = result["content"][0]["text"]
                    print(f"  ✅ is_prime({n}) = {content}")
                else:
                    print(f"  ✅ is_prime({n}) = {result}")
            except Exception as e:
                print(f"  ❌ is_prime({n}) failed: {e}")

        # Test with forced streaming
        print("\n🌊 Forced streaming example:")
        try:
            print("🔍 Computing next_prime(10000) with forced streaming...")
            result = await client.call_tool(
                "next_prime", {"n": 10000}, force_streaming=True
            )

            if isinstance(result, dict) and "content" in result:
                content = result["content"][0]["text"]
                print(f"  ✅ next_prime(10000) = {content}")
            else:
                print(f"  ✅ next_prime(10000) = {result}")
        except Exception as e:
            print(f"  ❌ next_prime(10000) failed: {e}")

        # More operations
        basic_functions = [
            ("gcd", {"a": 48, "b": 18}),
            ("fibonacci", {"n": 20}),  # Might trigger streaming
            ("lcm", {"a": 12, "b": 18}),
        ]

        print("\n🔐 Additional HTTP Operations:")
        for func_name, args in basic_functions:
            try:
                print(f"\n🔍 Computing {func_name}({args})...")
                result = await client.call_tool(func_name, args)

                if isinstance(result, dict) and "content" in result:
                    content = result["content"][0]["text"]
                    print(f"  ✅ {func_name}({args}) = {content}")
                else:
                    print(f"  ✅ {func_name}({args}) = {result}")
            except Exception as e:
                print(f"  ❌ {func_name}({args}) failed: {e}")

    except Exception as e:
        print(f"❌ HTTP number theory demonstration failed: {e}")
    finally:
        await client.stop()


async def demonstrate_http_arithmetic():
    """Demonstrate arithmetic functions via HTTP."""
    print("\n🧮 HTTP Arithmetic Demonstrations")
    print("=" * 50)

    client = MCPMathHTTPClient()

    try:
        await client.start()
        await client.initialize()

        # Get health info
        try:
            health = await client.get_health()
            print(
                f"💓 Server health: {health.get('status', 'unknown')} (score: {health.get('health_score', 0)})"
            )
        except Exception as e:
            print(f"⚠️ Could not get health info: {e}")

        # Basic operations
        print("\n📊 Basic HTTP Operations:")

        operations = [
            ("add", {"a": 123, "b": 456}),
            ("multiply", {"a": 17, "b": 23}),
            ("power", {"base": 3, "exponent": 8}),
            ("sqrt", {"x": 256}),
        ]

        for op_name, args in operations:
            try:
                print(f"\n🔍 Computing {op_name}({args})...")
                result = await client.call_tool(op_name, args)

                if isinstance(result, dict) and "content" in result:
                    content = result["content"][0]["text"]
                    print(f"  ✅ {op_name}({args}) = {content}")
                else:
                    print(f"  ✅ {op_name}({args}) = {result}")
            except Exception as e:
                print(f"  ❌ {op_name}({args}) failed: {e}")

    except Exception as e:
        print(f"❌ HTTP arithmetic demonstration failed: {e}")
    finally:
        await client.stop()


async def test_http_server_connectivity(port: int = 8000):
    """Test basic HTTP server connectivity."""
    print(f"\n🌐 Testing HTTP Server Connectivity (port {port})")
    print("=" * 50)

    client = MCPMathHTTPClient(f"http://localhost:{port}")

    try:
        await client.start()

        print("🔗 Testing server endpoints...")

        # Test root endpoint
        try:
            server_info = await client.get_server_info()
            print(f"✅ Root endpoint: {server_info.get('server', 'unknown')}")
        except Exception as e:
            print(f"❌ Root endpoint failed: {e}")
            return False

        # Test health endpoint
        try:
            health = await client.get_health()
            print(f"✅ Health endpoint: {health.get('status', 'unknown')}")
        except Exception as e:
            print(f"❌ Health endpoint failed: {e}")

        # Test MCP initialization
        try:
            init_result = await client.initialize()
            print("✅ MCP initialization successful")
            print(
                f"📋 Server: {init_result.get('serverInfo', {}).get('name', 'unknown')}"
            )
        except Exception as e:
            print(f"❌ MCP initialization failed: {e}")
            return False

        # Test tool listing
        try:
            tools = await client.list_tools()
            print(f"✅ Tool listing: {len(tools)} tools available")
        except Exception as e:
            print(f"❌ Tool listing failed: {e}")
            return False

        # Test simple calculation
        try:
            result = await client.call_tool(
                "add", {"a": 7, "b": 13}, force_streaming=False
            )
            print("✅ Simple calculation successful")
            print(f"🧮 add(7, 13) = {result}")
        except Exception as e:
            print(f"❌ Simple calculation failed: {e}")
            return False

        print("✅ HTTP server is fully functional!")
        return True

    except Exception as e:
        print(f"❌ HTTP connectivity test failed: {e}")
        return False
    finally:
        await client.stop()


async def main():
    """Main HTTP demonstration function."""
    print("🌐 Chuk MCP Math Server - HTTP Client Examples")
    print("=" * 60)

    if not _http_available:
        print("❌ HTTP client requires httpx: pip install httpx")
        return

    port = 8000
    server_process = None

    try:
        # Start HTTP server
        server_process = await start_http_server(port)

        # Test connectivity
        server_works = await test_http_server_connectivity(port)

        if server_works:
            print("\n🎯 Running full HTTP demonstrations...")
            await demonstrate_http_number_theory()
            await demonstrate_http_arithmetic()
            print("\n✅ All HTTP demonstrations completed!")
        else:
            print("\n❌ HTTP server connectivity failed")

    except Exception as e:
        print(f"❌ HTTP demonstration failed: {e}")
    finally:
        # Clean up server
        if server_process:
            print("\n🛑 Stopping HTTP server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
                server_process.wait()
            print("✅ HTTP server stopped")


if __name__ == "__main__":
    asyncio.run(main())
