#!/usr/bin/env python3
# src/chuk_mcp_math_server/base_server.py
"""
Generic MCP server base class that can be extended for different domains.
"""

import asyncio
import json
import logging
import sys
import time
from typing import Dict, Any, Optional, Callable, Protocol
from abc import ABC, abstractmethod

# Import the MCP server frameworks
try:
    from chuk_mcp.server import MCPServer
    from chuk_mcp.protocol.types import ServerCapabilities
    from chuk_mcp import JSONRPCMessage
    _chuk_mcp_available = True
except ImportError:
    _chuk_mcp_available = False

from .config import ServerConfig

logger = logging.getLogger(__name__)

class ToolHandler(Protocol):
    """Protocol for tool handlers."""
    async def __call__(self, **kwargs) -> Any: ...

class BaseMCPServer(ABC):
    """Generic base class for MCP servers with configurable capabilities."""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        
        # Configure logging
        log_level = getattr(logging, config.log_level.upper())
        logging.getLogger().setLevel(log_level)
        
        # Server capabilities based on configuration
        capabilities = ServerCapabilities(
            tools={"listChanged": True} if config.enable_tools else None,
            resources={"listChanged": True} if config.enable_resources else None,
            prompts={"listChanged": True} if config.enable_prompts else None
        )
        
        if _chuk_mcp_available:
            self.mcp_server = MCPServer(
                name=config.server_name,
                version=config.server_version,
                capabilities=capabilities
            )
        else:
            self.mcp_server = None
        
        # Initialize based on configuration
        self._initialize_server()
        
        logger.info(f"Base MCP Server initialized: {config.server_name}")
    
    def _initialize_server(self):
        """Initialize server components based on configuration."""
        if self.config.enable_tools:
            self._register_tools()
        
        if self.config.enable_resources:
            self._register_resources()
        
        if self.config.enable_prompts:
            self._register_prompts()
    
    @abstractmethod
    def _register_tools(self):
        """Register domain-specific tools. Must be implemented by subclasses."""
        pass
    
    def _register_resources(self):
        """Register server resources (can be overridden by subclasses)."""
        if not self.mcp_server or not hasattr(self.mcp_server, 'register_resource'):
            logger.warning("MCPServer does not support register_resource - skipping")
            return
        
        # Server configuration resource
        async def server_config():
            config_dict = self.config.to_dict()
            
            return json.dumps({
                "configuration": config_dict,
                "server_info": {
                    "name": self.config.server_name,
                    "version": self.config.server_version,
                    "description": self.config.server_description
                },
                "capabilities": {
                    "tools_enabled": self.config.enable_tools,
                    "prompts_enabled": self.config.enable_prompts,
                    "resources_enabled": self.config.enable_resources
                }
            }, indent=2)
        
        try:
            self.mcp_server.register_resource(
                uri=f"{self.config.server_name}://server-config",
                handler=server_config,
                name="Server Configuration",
                description="Current server configuration and status",
                mime_type="application/json"
            )
            logger.info("Registered base server resources")
        except Exception as e:
            logger.warning(f"Failed to register resources: {e}")
    
    def _register_prompts(self):
        """Register server prompts (can be overridden by subclasses)."""
        # Default implementation - subclasses can override
        logger.debug("No prompts registered in base server")
    
    def register_tool(self, name: str, handler: ToolHandler, schema: Dict[str, Any], description: str = ""):
        """Register a tool with the MCP server."""
        if not self.mcp_server:
            logger.warning("Cannot register tool - MCP server unavailable")
            return
        
        try:
            self.mcp_server.register_tool(
                name=name,
                handler=self._create_wrapped_handler(handler),
                schema=schema,
                description=description
            )
            logger.debug(f"Registered tool: {name}")
        except Exception as e:
            logger.error(f"Failed to register tool {name}: {e}")
    
    def _create_wrapped_handler(self, handler: ToolHandler) -> ToolHandler:
        """Create a wrapped handler with timeout and error handling."""
        async def wrapped_handler(**kwargs):
            try:
                # Apply computation timeout
                if self.config.computation_timeout > 0:
                    async with asyncio.timeout(self.config.computation_timeout):
                        return await handler(**kwargs)
                else:
                    return await handler(**kwargs)
                    
            except asyncio.TimeoutError:
                logger.warning(f"Handler timed out after {self.config.computation_timeout}s")
                return f"Computation timed out after {self.config.computation_timeout} seconds"
            except Exception as e:
                logger.error(f"Error in handler: {e}")
                return f"Error: {str(e)}"
        
        return wrapped_handler
    
    async def run_stdio(self):
        """Run the server using stdio transport."""
        if not self.mcp_server:
            logger.error("MCP server not available for stdio transport")
            return
        
        logger.info(f"🚀 Starting {self.config.server_name} (stdio)")
        
        try:
            # Manual stdio handling
            while True:
                try:
                    # Read message from stdin
                    line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                    if not line:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    logger.debug(f"Received: {line}")
                    
                    # Parse JSON-RPC message
                    try:
                        message_data = json.loads(line)
                        
                        # Create JSONRPCMessage
                        try:
                            message = JSONRPCMessage(**message_data)
                        except Exception:
                            if 'method' in message_data:
                                message = JSONRPCMessage(
                                    jsonrpc=message_data.get('jsonrpc', '2.0'),
                                    id=message_data.get('id'),
                                    method=message_data['method'],
                                    params=message_data.get('params')
                                )
                            else:
                                logger.error(f"Cannot create JSONRPCMessage from: {message_data}")
                                continue
                                
                    except Exception as e:
                        logger.error(f"Failed to parse message: {e}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {"code": -32700, "message": "Parse error"}
                        }
                        print(json.dumps(error_response), flush=True)
                        continue
                    
                    # Handle the message
                    try:
                        handler_result = self.mcp_server.protocol_handler.handle_message(message)
                        
                        # Check if it's a coroutine and await if needed
                        if hasattr(handler_result, '__await__'):
                            response, session_id = await handler_result
                        else:
                            response, session_id = handler_result
                        
                        # Send response if there is one
                        if response:
                            # Convert response to dict if it's a Pydantic model
                            if hasattr(response, 'model_dump'):
                                response_dict = response.model_dump()
                            elif hasattr(response, 'dict'):
                                response_dict = response.dict()
                            else:
                                response_dict = response
                            
                            response_json = json.dumps(response_dict)
                            logger.debug(f"Sending: {response_json}")
                            print(response_json, flush=True)
                        else:
                            logger.debug("No response required for this message")
                            
                    except Exception as e:
                        logger.error(f"Error handling message: {e}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": message_data.get('id'),
                            "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                        }
                        print(json.dumps(error_response), flush=True)
                    
                except Exception as e:
                    logger.error(f"Error in stdio loop: {e}")
                    break
                    
        except KeyboardInterrupt:
            logger.info("Server interrupted")
        except Exception as e:
            logger.error(f"Error in stdio server: {e}")
    
    async def run_http(self):
        """Run the server using HTTP transport."""
        try:
            # Import FastAPI dependencies
            try:
                from fastapi import FastAPI, Request
                from fastapi.responses import JSONResponse
                from fastapi.middleware.cors import CORSMiddleware
                import uvicorn
            except ImportError:
                logger.error("HTTP transport requires FastAPI and uvicorn: pip install fastapi uvicorn")
                return
            
            # Create FastAPI app
            app = FastAPI(
                title=self.config.server_name,
                version=self.config.server_version,
                description=self.config.server_description
            )
            
            # Add CORS if enabled
            if self.config.enable_cors:
                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
            
            # Root endpoint
            @app.get("/")
            async def root():
                return {
                    "server": self.config.server_name,
                    "version": self.config.server_version,
                    "description": self.config.server_description,
                    "transport": "http"
                }
            
            # Health endpoint
            @app.get("/health")
            async def health():
                return {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "server": self.config.server_name
                }
            
            # MCP endpoint
            @app.post("/mcp")
            async def handle_mcp(request: Request):
                try:
                    message_data = await request.json()
                    
                    # Create JSONRPCMessage
                    message = JSONRPCMessage(
                        jsonrpc=message_data.get('jsonrpc', '2.0'),
                        id=message_data.get('id'),
                        method=message_data['method'],
                        params=message_data.get('params')
                    )
                    
                    # Handle the message
                    handler_result = self.mcp_server.protocol_handler.handle_message(message)
                    
                    # Check if it's a coroutine and await if needed
                    if hasattr(handler_result, '__await__'):
                        response, session_id = await handler_result
                    else:
                        response, session_id = handler_result
                    
                    # Convert response to dict
                    if response:
                        if hasattr(response, 'model_dump'):
                            response_dict = response.model_dump()
                        elif hasattr(response, 'dict'):
                            response_dict = response.dict()
                        else:
                            response_dict = response
                        
                        return JSONResponse(content=response_dict)
                    else:
                        return JSONResponse(content={"status": "accepted"}, status_code=202)
                
                except Exception as e:
                    logger.error(f"Error handling HTTP MCP request: {e}")
                    return JSONResponse(
                        content={
                            "jsonrpc": "2.0",
                            "id": message_data.get('id') if 'message_data' in locals() else None,
                            "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                        },
                        status_code=500
                    )
            
            logger.info(f"🌐 Starting {self.config.server_name} (HTTP)")
            logger.info(f"📍 Server URL: http://{self.config.host}:{self.config.port}")
            logger.info(f"🎯 MCP endpoint: http://{self.config.host}:{self.config.port}/mcp")
            
            # Run the server
            config = uvicorn.Config(
                app, 
                host=self.config.host, 
                port=self.config.port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            logger.error(f"Error in HTTP server: {e}")
            import traceback
            traceback.print_exc()
    
    async def run(self):
        """Run the server with the configured transport."""
        if self.config.transport == "stdio":
            await self.run_stdio()
        elif self.config.transport == "http":
            await self.run_http()
        else:
            logger.error(f"Unknown transport: {self.config.transport}")
    
    def convert_to_json_schema(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Convert function parameters to JSON schema format."""
        if not parameters:
            return {"type": "object", "properties": {}}
        
        properties = {}
        required = []
        
        for param_name, param_spec in parameters.items():
            if isinstance(param_spec, dict):
                # Get the type from the param_spec
                param_type = param_spec.get("type", "string")
                
                # Map our types to valid JSON schema types
                if param_type in ["integer", "int"]:
                    json_type = "integer"
                elif param_type in ["number", "float"]:
                    json_type = "number"
                elif param_type == "boolean":
                    json_type = "boolean"
                elif param_type == "string":
                    json_type = "string"
                elif param_type == "array":
                    json_type = "array"
                else:
                    # Default to string for any unrecognized type
                    json_type = "string"
                
                # Create proper JSON schema property
                property_schema = {
                    "type": json_type,
                    "description": f"Parameter: {param_name}"
                }
                
                # Add additional constraints if available
                if "description" in param_spec:
                    property_schema["description"] = param_spec["description"]
                
                properties[param_name] = property_schema
                
                # Check if required
                if param_spec.get("required", False):
                    required.append(param_name)
            else:
                # If param_spec is not a dict, create a basic string parameter
                properties[param_name] = {
                    "type": "string",
                    "description": f"Parameter: {param_name}"
                }
        
        schema = {
            "type": "object",
            "properties": properties
        }
        
        if required:
            schema["required"] = required
        
        return schema