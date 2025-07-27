#!/usr/bin/env python3
# debug/debug_server_response.py
"""
Debug what the server is actually sending in response to messages.
"""

import asyncio
import subprocess
import sys
import json
from pathlib import Path

async def debug_server_response():
    """Debug server responses step by step."""
    print("🔍 Debug Server Response")
    print("=" * 30)
    
    # Find server path
    current_dir = Path(__file__).parent
    server_paths = [
        current_dir.parent / "src" / "chuk_mcp_math_server" / "math_server.py",
        "src/chuk_mcp_math_server/math_server.py",
    ]
    
    server_path = None
    for path in server_paths:
        if Path(path).exists():
            server_path = str(path)
            break
    
    if not server_path:
        server_cmd = ["python", "-m", "chuk_mcp_math_server.math_server", "--transport", "stdio"]
        print("📍 Using module execution")
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
        await asyncio.sleep(3)
        
        # Check if running
        if process.returncode is not None:
            stderr = await process.stderr.read()
            print(f"❌ Server failed to start: {stderr.decode()}")
            return False
        
        print("✅ Server started successfully")
        
        # Send initialize message
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "clientInfo": {"name": "debug-client"}
            }
        }
        
        print(f"📤 Sending: {json.dumps(init_msg)}")
        msg_json = json.dumps(init_msg) + "\n"
        process.stdin.write(msg_json.encode())
        await process.stdin.drain()
        
        # Read response with detailed debugging
        print("📥 Waiting for response...")
        try:
            response_line = await asyncio.wait_for(
                process.stdout.readline(), 
                timeout=15.0
            )
            
            if response_line:
                response_text = response_line.decode().strip()
                print(f"📥 Raw response: '{response_text}'")
                
                if response_text:
                    try:
                        response = json.loads(response_text)
                        print(f"📥 Parsed response: {json.dumps(response, indent=2)}")
                        
                        if response.get("error") is not None:
                            print(f"❌ Server returned error: {response['error']}")
                            return False
                        elif "result" in response:
                            print(f"✅ Server returned successful result")
                            return True
                        else:
                            print(f"⚠️ Response has no result or error field")
                            return False
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse JSON: {e}")
                        return False
                else:
                    print(f"❌ Empty response")
                    return False
            else:
                print(f"❌ No response line received")
                return False
                
        except asyncio.TimeoutError:
            print(f"❌ Response timeout")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'process' in locals():
            try:
                process.terminate()
                await process.wait()
            except:
                pass

if __name__ == "__main__":
    success = asyncio.run(debug_server_response())
    sys.exit(0 if success else 1)