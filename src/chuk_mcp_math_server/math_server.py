#!/usr/bin/env python3
# src/chuk_mcp_math_server/math_server.py
"""
Configurable Chuk MCP Math Server - Compatible with chuk-mcp v0.4.0

Provides comprehensive configuration options for customizing which mathematical
functions, tools, prompts, and resources are exposed via the MCP server.
"""

import asyncio
import argparse
import logging
import sys
import os
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

# Try to import YAML support
try:
    import yaml
    _yaml_available = True
except ImportError:
    _yaml_available = False

# Import the MCP server frameworks
try:
    from chuk_mcp.server import MCPServer
    from chuk_mcp.protocol.types import ServerCapabilities
    from chuk_mcp import JSONRPCMessage
    _chuk_mcp_available = True
except ImportError:
    _chuk_mcp_available = False
    print("Warning: chuk-mcp not available")

# Import our comprehensive math library
try:
    import chuk_mcp_math
    from chuk_mcp_math import get_mcp_functions
    _math_library_available = True
except ImportError as e:
    print(f"Error: Could not import chuk_mcp_math: {e}")
    _math_library_available = False
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

def _get_package_version():
    """Get package version dynamically."""
    try:
        from ._version import __version__
        return __version__
    except (ImportError, AttributeError):
        pass
    
    try:
        from importlib.metadata import version, PackageNotFoundError
        return version("chuk-mcp-math-server")
    except (ImportError, PackageNotFoundError):
        pass
    
    # Fallback to pyproject.toml parsing
    try:
        from pathlib import Path
        import re
        
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text()
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
    except:
        pass
    
    return "0.1.0"

@dataclass
class ServerConfig:
    """Comprehensive server configuration with all customization options."""
    
    # Transport settings
    transport: str = "stdio"
    port: int = 8000
    host: str = "0.0.0.0"
    
    # Global feature toggles
    enable_tools: bool = True
    enable_prompts: bool = True
    enable_resources: bool = True
    
    # Function filtering
    function_whitelist: List[str] = field(default_factory=list)
    function_blacklist: List[str] = field(default_factory=list)
    domain_whitelist: List[str] = field(default_factory=list)
    domain_blacklist: List[str] = field(default_factory=list)
    category_whitelist: List[str] = field(default_factory=list)
    category_blacklist: List[str] = field(default_factory=list)
    
    # Performance settings
    cache_strategy: str = "smart"
    cache_size: int = 1000
    max_concurrent_calls: int = 10
    computation_timeout: float = 30.0
    
    # Logging and debugging
    log_level: str = "INFO"
    verbose: bool = False
    quiet: bool = False
    
    # Security settings
    enable_cors: bool = True
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 60
    
    # Server metadata
    server_name: str = "chuk-mcp-math-server"
    server_version: str = field(default_factory=_get_package_version)
    server_description: str = "Configurable mathematical computation server"
    
    # Advanced options
    streaming_threshold: int = 1000
    memory_limit_mb: int = 512
    custom_config_path: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration values."""
        if self.transport not in ["stdio", "http"]:
            raise ValueError(f"Invalid transport: {self.transport}")
        
        if not (1 <= self.port <= 65535):
            raise ValueError(f"Invalid port: {self.port}")
        
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            raise ValueError(f"Invalid log level: {self.log_level}")
        
        if self.cache_strategy not in ["none", "memory", "smart"]:
            raise ValueError(f"Invalid cache strategy: {self.cache_strategy}")
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ServerConfig':
        """Load configuration from file (YAML or JSON)."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            if config_path.suffix.lower() in ['.yml', '.yaml']:
                if not _yaml_available:
                    raise ImportError("PyYAML required for YAML config files: pip install pyyaml")
                data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> 'ServerConfig':
        """Load configuration from environment variables."""
        env_mapping = {
            'MCP_MATH_TRANSPORT': 'transport',
            'MCP_MATH_PORT': ('port', int),
            'MCP_MATH_HOST': 'host',
            'MCP_MATH_ENABLE_TOOLS': ('enable_tools', lambda x: x.lower() == 'true'),
            'MCP_MATH_ENABLE_PROMPTS': ('enable_prompts', lambda x: x.lower() == 'true'),
            'MCP_MATH_ENABLE_RESOURCES': ('enable_resources', lambda x: x.lower() == 'true'),
            'MCP_MATH_FUNCTION_WHITELIST': ('function_whitelist', lambda x: x.split(',')),
            'MCP_MATH_FUNCTION_BLACKLIST': ('function_blacklist', lambda x: x.split(',')),
            'MCP_MATH_DOMAIN_WHITELIST': ('domain_whitelist', lambda x: x.split(',')),
            'MCP_MATH_DOMAIN_BLACKLIST': ('domain_blacklist', lambda x: x.split(',')),
            'MCP_MATH_CACHE_STRATEGY': 'cache_strategy',
            'MCP_MATH_CACHE_SIZE': ('cache_size', int),
            'MCP_MATH_LOG_LEVEL': 'log_level',
            'MCP_MATH_TIMEOUT': ('computation_timeout', float),
            'MCP_MATH_MAX_CONCURRENT': ('max_concurrent_calls', int),
        }
        
        config_data = {}
        for env_key, config_field in env_mapping.items():
            if env_key in os.environ:
                if isinstance(config_field, tuple):
                    field_name, converter = config_field
                    try:
                        config_data[field_name] = converter(os.environ[env_key])
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid value for {env_key}: {e}")
                else:
                    config_data[config_field] = os.environ[env_key]
        
        return cls(**config_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
    
    def save_to_file(self, config_path: str, format: str = "yaml"):
        """Save configuration to file."""
        config_data = self.to_dict()
        
        with open(config_path, 'w') as f:
            if format.lower() == "yaml":
                if not _yaml_available:
                    raise ImportError("PyYAML required for YAML output: pip install pyyaml")
                yaml.dump(config_data, f, default_flow_style=False)
            elif format.lower() == "json":
                json.dump(config_data, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")

class FunctionFilter:
    """Filters mathematical functions based on configuration criteria."""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self._all_functions = None
        self._filtered_functions = None
    
    def get_all_functions(self) -> Dict[str, Any]:
        """Get all available mathematical functions."""
        if self._all_functions is None:
            try:
                # Try the sync version first
                self._all_functions = get_mcp_functions()
                
                # If that returns empty, try to load from individual modules
                if len(self._all_functions) == 0:
                    logger.warning("get_mcp_functions() returned 0 functions, trying direct module access")
                    self._all_functions = self._load_functions_directly()
                    
            except Exception as e:
                logger.error(f"Error loading functions: {e}")
                self._all_functions = {}
                
        return self._all_functions
    
    def _load_functions_directly(self) -> Dict[str, Any]:
        """Load functions directly from modules if get_mcp_functions fails."""
        functions = {}
        
        try:
            # Import the modules
            from chuk_mcp_math import arithmetic, number_theory
            
            # Get arithmetic functions
            for attr_name in dir(arithmetic):
                if not attr_name.startswith('_') and callable(getattr(arithmetic, attr_name)):
                    func = getattr(arithmetic, attr_name)
                    if hasattr(func, '__name__') and not attr_name in ['get_module_info', 'get_reorganized_modules', 'print_reorganized_status']:
                        # Create a mock function spec
                        qualified_name = f"arithmetic::{attr_name}"
                        functions[qualified_name] = self._create_mock_function_spec(attr_name, "arithmetic", "core", func)
            
            # Get number theory functions  
            for attr_name in dir(number_theory):
                if not attr_name.startswith('_') and callable(getattr(number_theory, attr_name)):
                    func = getattr(number_theory, attr_name)
                    if hasattr(func, '__name__') and not attr_name in ['get_module_info', 'get_reorganized_modules', 'print_reorganized_status']:
                        # Create a mock function spec
                        qualified_name = f"number_theory::{attr_name}"
                        functions[qualified_name] = self._create_mock_function_spec(attr_name, "number_theory", "primes", func)
            
            logger.info(f"Loaded {len(functions)} functions directly from modules")
            
        except Exception as e:
            logger.error(f"Error loading functions directly: {e}")
            
        return functions
    
    def _create_mock_function_spec(self, name: str, namespace: str, category: str, func):
        """Create a mock function spec for direct module loading."""
        import inspect
        
        # Create a simple spec object
        class MockFunctionSpec:
            def __init__(self, name, namespace, category, func):
                self.function_name = name
                self.namespace = namespace
                self.category = category
                self.description = f"{name} function from {namespace}"
                self.function_ref = func
                # All functions from chuk_mcp_math appear to be async
                self.is_async_native = True  # Force to True since all functions are coroutines
                self.cache_strategy = "none"
                
                # Try to extract parameters from function signature
                try:
                    sig = inspect.signature(func)
                    self.parameters = {}
                    for param_name, param in sig.parameters.items():
                        if param.annotation != inspect.Parameter.empty:
                            param_type = str(param.annotation).replace('<class \'', '').replace('\'>', '')
                            if 'Union' in param_type:
                                param_type = "number"  # Simplify Union types
                            elif 'int' in param_type.lower():
                                param_type = "integer"
                            elif 'float' in param_type.lower():
                                param_type = "number"
                            elif 'bool' in param_type.lower():
                                param_type = "boolean"
                            elif 'str' in param_type.lower():
                                param_type = "string"
                            self.parameters[param_name] = {"type": param_type}
                        else:
                            self.parameters[param_name] = {"type": "any"}
                except:
                    self.parameters = {}
        
        return MockFunctionSpec(name, namespace, category, func)
    
    def get_filtered_functions(self) -> Dict[str, Any]:
        """Get functions filtered according to configuration."""
        if self._filtered_functions is None:
            self._filtered_functions = self._apply_filters()
        return self._filtered_functions
    
    def _apply_filters(self) -> Dict[str, Any]:
        """Apply all configured filters to the function list."""
        all_functions = self.get_all_functions()
        filtered = {}
        
        for qualified_name, func_spec in all_functions.items():
            if self._should_include_function(func_spec):
                filtered[qualified_name] = func_spec
        
        logger.info(f"Filtered {len(all_functions)} functions down to {len(filtered)}")
        return filtered
    
    def _should_include_function(self, func_spec) -> bool:
        """Determine if a function should be included based on filters."""
        
        # Check function whitelist (if specified, only these are allowed)
        if self.config.function_whitelist:
            if func_spec.function_name not in self.config.function_whitelist:
                return False
        
        # Check function blacklist
        if func_spec.function_name in self.config.function_blacklist:
            return False
        
        # Check domain whitelist (if specified, only these domains are allowed)
        if self.config.domain_whitelist:
            if func_spec.namespace not in self.config.domain_whitelist:
                return False
        
        # Check domain blacklist
        if func_spec.namespace in self.config.domain_blacklist:
            return False
        
        # Check category whitelist (if specified, only these categories are allowed)
        if self.config.category_whitelist:
            if func_spec.category not in self.config.category_whitelist:
                return False
        
        # Check category blacklist
        if func_spec.category in self.config.category_blacklist:
            return False
        
        return True
    
    def get_function_stats(self) -> Dict[str, Any]:
        """Get statistics about function filtering."""
        all_functions = self.get_all_functions()
        filtered_functions = self.get_filtered_functions()
        
        # Count by domain
        all_domains = {}
        filtered_domains = {}
        
        for func_spec in all_functions.values():
            domain = func_spec.namespace
            all_domains[domain] = all_domains.get(domain, 0) + 1
        
        for func_spec in filtered_functions.values():
            domain = func_spec.namespace
            filtered_domains[domain] = filtered_domains.get(domain, 0) + 1
        
        # Avoid division by zero
        total_available = len(all_functions)
        total_filtered = len(filtered_functions)
        filter_ratio = total_filtered / total_available if total_available > 0 else 0
        
        return {
            "total_available": total_available,
            "total_filtered": total_filtered,
            "filter_ratio": filter_ratio,
            "domains_available": all_domains,
            "domains_filtered": filtered_domains,
            "filtering_active": bool(
                self.config.function_whitelist or 
                self.config.function_blacklist or
                self.config.domain_whitelist or 
                self.config.domain_blacklist or
                self.config.category_whitelist or 
                self.config.category_blacklist
            )
        }

class ConfigurableMCPMathServer:
    """Highly configurable MCP Math Server with granular control over exposed functionality."""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.function_filter = FunctionFilter(config)
        
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
        
        logger.info(f"Configurable MCP Math Server initialized")
        logger.info(f"Config: Tools={config.enable_tools}, Prompts={config.enable_prompts}, Resources={config.enable_resources}")
    
    def _initialize_server(self):
        """Initialize server components based on configuration."""
        if self.config.enable_tools:
            self._register_math_tools()
        
        if self.config.enable_resources:
            self._register_math_resources()
        
        # Log filtering statistics
        stats = self.function_filter.get_function_stats()
        logger.info(f"Function filtering: {stats['total_filtered']}/{stats['total_available']} functions exposed")
        
        if stats['filtering_active']:
            logger.info(f"Active filters - Domains: {list(stats['domains_filtered'].keys())}")
    
    def _register_math_tools(self):
        """Register filtered mathematical functions as MCP tools."""
        if not self.mcp_server or not _math_library_available:
            logger.warning("Cannot register math tools - server or library unavailable")
            return
        
        # Get filtered functions
        filtered_functions = self.function_filter.get_filtered_functions()
        
        registered_count = 0
        for qualified_name, func_spec in filtered_functions.items():
            try:
                # Register the tool with the MCP server
                self.mcp_server.register_tool(
                    name=func_spec.function_name,
                    handler=self._create_math_handler(func_spec),
                    schema=self._convert_to_json_schema(func_spec.parameters),
                    description=f"{func_spec.description} (Domain: {func_spec.namespace}, Category: {func_spec.category})"
                )
                registered_count += 1
                
            except Exception as e:
                logger.error(f"Failed to register tool {qualified_name}: {e}")
        
        logger.info(f"Registered {registered_count} mathematical tools")
    
    def _create_math_handler(self, func_spec):
        """Create an async handler for a mathematical function with timeout support."""
        async def handler(**kwargs):
            try:
                # Apply computation timeout
                if self.config.computation_timeout > 0:
                    async with asyncio.timeout(self.config.computation_timeout):
                        return await self._execute_function(func_spec, kwargs)
                else:
                    return await self._execute_function(func_spec, kwargs)
                    
            except asyncio.TimeoutError:
                logger.warning(f"Function {func_spec.function_name} timed out after {self.config.computation_timeout}s")
                return f"Computation timed out after {self.config.computation_timeout} seconds"
            except Exception as e:
                logger.error(f"Error executing {func_spec.function_name}: {e}")
                return f"Error: {str(e)}"
        
        return handler
    
    async def _execute_function(self, func_spec, kwargs):
        """Execute a mathematical function with proper async handling."""
        if func_spec.function_ref:
            # All functions from chuk_mcp_math are async, so always await them
            try:
                if func_spec.is_async_native or hasattr(func_spec.function_ref, '__call__'):
                    # Check if it's actually a coroutine function
                    import inspect
                    if inspect.iscoroutinefunction(func_spec.function_ref):
                        result = await func_spec.function_ref(**kwargs)
                    else:
                        result = func_spec.function_ref(**kwargs)
                else:
                    result = await func_spec.function_ref(**kwargs)
                
                return result
            except Exception as e:
                logger.error(f"Error executing {func_spec.function_name}: {e}")
                return f"Error: {str(e)}"
        else:
            return f"Function reference not available for {func_spec.function_name}"
    
    def _convert_to_json_schema(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
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
    
    
    def _register_math_resources(self):
        """Register mathematical resources with configuration info."""
        if not self.mcp_server:
            return
        
        # Check if register_resource method exists
        if not hasattr(self.mcp_server, 'register_resource'):
            logger.warning("MCPServer does not support register_resource - skipping resource registration")
            return
        
        # Server configuration resource
        async def server_config():
            config_dict = self.config.to_dict()
            stats = self.function_filter.get_function_stats()
            
            return json.dumps({
                "configuration": config_dict,
                "function_filtering": stats,
                "server_info": {
                    "name": self.config.server_name,
                    "version": self.config.server_version,
                    "description": self.config.server_description
                },
                "capabilities": {
                    "tools_enabled": self.config.enable_tools,
                    "prompts_enabled": self.config.enable_prompts,
                    "resources_enabled": self.config.enable_resources
                },
                "functions_available": stats["total_filtered"]
            }, indent=2)
        
        try:
            self.mcp_server.register_resource(
                uri="math://server-config",
                handler=server_config,
                name="Server Configuration",
                description="Current server configuration and filtering statistics",
                mime_type="application/json"
            )
            
            # Available functions list
            async def available_functions():
                filtered_functions = self.function_filter.get_filtered_functions()
                
                functions_by_domain = {}
                for func_spec in filtered_functions.values():
                    domain = func_spec.namespace
                    if domain not in functions_by_domain:
                        functions_by_domain[domain] = []
                    
                    functions_by_domain[domain].append({
                        "name": func_spec.function_name,
                        "description": func_spec.description,
                        "category": func_spec.category,
                        "async_native": func_spec.is_async_native,
                        "cached": func_spec.cache_strategy != "none"
                    })
                
                return json.dumps({
                    "total_functions": len(filtered_functions),
                    "functions_by_domain": functions_by_domain,
                    "filtering_applied": self.function_filter.get_function_stats()["filtering_active"]
                }, indent=2)
            
            self.mcp_server.register_resource(
                uri="math://available-functions",
                handler=available_functions,
                name="Available Functions",
                description="List of currently available mathematical functions after filtering",
                mime_type="application/json"
            )
            
            logger.info("Registered mathematical resources")
            
        except Exception as e:
            logger.warning(f"Failed to register resources: {e}")
    
    async def run_stdio(self):
        """Run the server using stdio transport with manual message handling."""
        if not self.mcp_server:
            logger.error("MCP server not available for stdio transport")
            return
        
        logger.info(f"🧮 Starting {self.config.server_name} (stdio transport)")
        stats = self.function_filter.get_function_stats()
        logger.info(f"📊 Serving {stats['total_filtered']} of {stats['total_available']} mathematical functions")
        
        try:
            # Manual stdio handling since the library doesn't provide run_stdio
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
                        
                        # Create JSONRPCMessage - handle different constructor patterns
                        try:
                            message = JSONRPCMessage(**message_data)
                        except Exception:
                            # Try different constructor approaches
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
                        # Send error response
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {"code": -32700, "message": "Parse error"}
                        }
                        print(json.dumps(error_response), flush=True)
                        continue
                    
                    # Handle the message
                    try:
                        # The handle_message method might be async, so await it
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
                            # Some messages don't expect responses (notifications)
                            logger.debug("No response required for this message")
                            
                    except Exception as e:
                        logger.error(f"Error handling message: {e}")
                        # Send error response
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
            # Try to import FastAPI and create HTTP server
            try:
                from fastapi import FastAPI, Request
                from fastapi.responses import JSONResponse
                from fastapi.middleware.cors import CORSMiddleware
                import uvicorn
            except ImportError:
                logger.error("HTTP transport requires FastAPI and uvicorn: pip install fastapi uvicorn")
                return
            
            # Create a simple FastAPI app for HTTP transport
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
                stats = self.function_filter.get_function_stats()
                return {
                    "server": self.config.server_name,
                    "version": self.config.server_version,
                    "description": self.config.server_description,
                    "transport": "http",
                    "functions_available": stats["total_filtered"],
                    "domains": list(stats["domains_filtered"].keys())
                }
            
            # Health endpoint
            @app.get("/health")
            async def health():
                return {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "functions": self.function_filter.get_function_stats()["total_filtered"]
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
            
            logger.info(f"🧮 Starting {self.config.server_name} (HTTP transport)")
            logger.info(f"🌐 Server URL: http://{self.config.host}:{self.config.port}")
            stats = self.function_filter.get_function_stats()
            logger.info(f"📊 Serving {stats['total_filtered']} of {stats['total_available']} mathematical functions")
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

def load_configuration(args) -> ServerConfig:
    """Load configuration from multiple sources with proper precedence."""
    
    # Start with defaults
    config = ServerConfig()
    
    # Load from file if specified
    if args.config:
        try:
            file_config = ServerConfig.from_file(args.config)
            # Merge file config with defaults
            for key, value in file_config.to_dict().items():
                if key != "custom_config_path":
                    setattr(config, key, value)
            logger.info(f"Loaded configuration from {args.config}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            sys.exit(1)
    
    # Override with environment variables
    try:
        env_config = ServerConfig.from_env()
        for key, value in env_config.to_dict().items():
            if value is not None and value != getattr(ServerConfig(), key):
                setattr(config, key, value)
        logger.debug("Applied environment variable overrides")
    except Exception as e:
        logger.warning(f"Error loading environment config: {e}")
    
    # Override with command line arguments
    cli_overrides = {
        'transport': args.transport,
        'port': args.port,
        'host': args.host,
        'enable_tools': not args.disable_tools,
        'enable_prompts': not args.disable_prompts,
        'enable_resources': not args.disable_resources,
        'verbose': args.verbose,
        'quiet': args.quiet,
        'cache_strategy': args.cache_strategy,
    }
    
    # Handle list arguments
    if args.functions:
        config.function_whitelist = args.functions
    if args.exclude_functions:
        config.function_blacklist = args.exclude_functions
    if args.domains:
        config.domain_whitelist = args.domains
    if args.exclude_domains:
        config.domain_blacklist = args.exclude_domains
    if args.categories:
        config.category_whitelist = args.categories
    if args.exclude_categories:
        config.category_blacklist = args.exclude_categories
    
    # Apply CLI overrides
    for key, value in cli_overrides.items():
        if value is not None:
            setattr(config, key, value)
    
    # Handle log level
    if args.verbose:
        config.log_level = "DEBUG"
    elif args.quiet:
        config.log_level = "WARNING"
    
    return config

def main():
    """Enhanced main entry point with comprehensive configuration support."""
    parser = argparse.ArgumentParser(
        description="Configurable Chuk MCP Math Server - Highly Customizable Mathematical Function Server",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Transport settings
    transport_group = parser.add_argument_group('Transport Settings')
    transport_group.add_argument(
        "--transport", "-t",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport method to use (default: stdio)"
    )
    transport_group.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port for HTTP transport (default: 8000)"
    )
    transport_group.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP transport (default: 0.0.0.0)"
    )
    
    # Feature toggles
    feature_group = parser.add_argument_group('Feature Control')
    feature_group.add_argument(
        "--disable-tools",
        action="store_true",
        help="Disable mathematical tool registration"
    )
    feature_group.add_argument(
        "--disable-prompts",
        action="store_true",
        help="Disable prompt registration"
    )
    feature_group.add_argument(
        "--disable-resources",
        action="store_true",
        help="Disable resource registration"
    )
    
    # Function filtering
    filter_group = parser.add_argument_group('Function Filtering')
    filter_group.add_argument(
        "--functions",
        nargs="+",
        help="Whitelist specific functions (e.g., --functions is_prime fibonacci)"
    )
    filter_group.add_argument(
        "--exclude-functions",
        nargs="+",
        help="Blacklist specific functions (e.g., --exclude-functions slow_function)"
    )
    filter_group.add_argument(
        "--domains",
        nargs="+",
        choices=["arithmetic", "number_theory", "trigonometry"],
        help="Whitelist mathematical domains"
    )
    filter_group.add_argument(
        "--exclude-domains",
        nargs="+",
        choices=["arithmetic", "number_theory", "trigonometry"],
        help="Blacklist mathematical domains"
    )
    filter_group.add_argument(
        "--categories",
        nargs="+",
        help="Whitelist function categories (e.g., --categories core primes)"
    )
    filter_group.add_argument(
        "--exclude-categories",
        nargs="+",
        help="Blacklist function categories"
    )
    
    # Performance settings
    perf_group = parser.add_argument_group('Performance Settings')
    perf_group.add_argument(
        "--cache-strategy",
        choices=["none", "memory", "smart"],
        default="smart",
        help="Caching strategy (default: smart)"
    )
    perf_group.add_argument(
        "--cache-size",
        type=int,
        default=1000,
        help="Cache size for mathematical functions (default: 1000)"
    )
    perf_group.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Computation timeout in seconds (default: 30.0)"
    )
    
    # Logging and debugging
    log_group = parser.add_argument_group('Logging')
    log_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging"
    )
    log_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimize logging output"
    )
    
    # Configuration file
    config_group = parser.add_argument_group('Configuration')
    config_group.add_argument(
        "--config", "-c",
        help="Load configuration from file (YAML or JSON)"
    )
    config_group.add_argument(
        "--save-config",
        help="Save current configuration to file and exit"
    )
    config_group.add_argument(
        "--show-config",
        action="store_true",
        help="Show current configuration and exit"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_configuration(args)
    
    # Handle special options
    if args.save_config:
        try:
            config.save_to_file(args.save_config)
            print(f"✅ Configuration saved to {args.save_config}")
            return
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            sys.exit(1)
    
    if args.show_config:
        print("📊 Current Configuration:")
        print(json.dumps(config.to_dict(), indent=2))
        return
    
    # Check library availability
    if not _math_library_available:
        logger.error("❌ chuk_mcp_math library not available")
        sys.exit(1)
    
    if config.transport == "stdio" and not _chuk_mcp_available:
        logger.error("❌ chuk-mcp framework required for stdio transport")
        sys.exit(1)
    
    try:
        # Create and run server
        server = ConfigurableMCPMathServer(config)
        
        logger.info("✨ Configurable MCP Math Server starting...")
        logger.info(f"🎯 Transport: {config.transport}")
        if config.transport == "http":
            logger.info(f"🌐 Host: {config.host}:{config.port}")
        
        # Show filtering info
        stats = server.function_filter.get_function_stats()
        if stats["filtering_active"]:
            logger.info(f"🔍 Function filtering active: {stats['total_filtered']}/{stats['total_available']} functions")
        else:
            logger.info(f"📊 All {stats['total_available']} functions available")
        
        asyncio.run(server.run())
        
    except KeyboardInterrupt:
        logger.info("🛑 Server interrupted by user")
    except Exception as e:
        logger.error(f"💥 Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()