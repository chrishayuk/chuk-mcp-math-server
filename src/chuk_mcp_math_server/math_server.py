#!/usr/bin/env python3
# src/chuk_mcp_math_server/math_server.py
"""
Mathematical MCP Server - extends the base server with math-specific functionality.
"""

import asyncio
import json
import logging
import inspect
from typing import Dict, Any

# Import our math library
try:
    import chuk_mcp_math
    _math_library_available = True
except ImportError as e:
    _math_library_available = False

from .base_server import BaseMCPServer
from .config import ServerConfig
from .function_filter import FunctionFilter

logger = logging.getLogger(__name__)

class ConfigurableMCPMathServer(BaseMCPServer):
    """MCP Math Server with granular control over exposed mathematical functionality."""
    
    def __init__(self, config: ServerConfig):
        self.function_filter = FunctionFilter(config)
        super().__init__(config)
        
        # Log math-specific initialization
        stats = self.function_filter.get_function_stats()
        logger.info(f"Math server initialized with {stats['total_filtered']}/{stats['total_available']} functions")
    
    def _register_tools(self):
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
                self.register_tool(
                    name=func_spec.function_name,
                    handler=self._create_math_handler(func_spec),
                    schema=self.convert_to_json_schema(func_spec.parameters),
                    description=f"{func_spec.description} (Domain: {func_spec.namespace}, Category: {func_spec.category})"
                )
                registered_count += 1
                
            except Exception as e:
                logger.error(f"Failed to register tool {qualified_name}: {e}")
        
        logger.info(f"Registered {registered_count} mathematical tools")
    
    def _create_math_handler(self, func_spec):
        """Create an async handler for a mathematical function."""
        async def handler(**kwargs):
            try:
                return await self._execute_function(func_spec, kwargs)
            except Exception as e:
                logger.error(f"Error executing {func_spec.function_name}: {e}")
                return f"Error: {str(e)}"
        
        return handler
    
    async def _execute_function(self, func_spec, kwargs):
        """Execute a mathematical function with proper async handling."""
        if func_spec.function_ref:
            try:
                # Check if it's actually a coroutine function
                if inspect.iscoroutinefunction(func_spec.function_ref):
                    result = await func_spec.function_ref(**kwargs)
                else:
                    result = func_spec.function_ref(**kwargs)
                
                return result
            except Exception as e:
                logger.error(f"Error executing {func_spec.function_name}: {e}")
                return f"Error: {str(e)}"
        else:
            return f"Function reference not available for {func_spec.function_name}"
    
    def _register_resources(self):
        """Register mathematical resources with configuration info."""
        # Call parent method first
        super()._register_resources()
        
        if not self.mcp_server or not hasattr(self.mcp_server, 'register_resource'):
            return
        
        try:
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
            
            # Function statistics
            async def function_stats():
                stats = self.function_filter.get_function_stats()
                return json.dumps(stats, indent=2)
            
            self.mcp_server.register_resource(
                uri="math://function-stats",
                handler=function_stats,
                name="Function Statistics",
                description="Statistics about function filtering and availability",
                mime_type="application/json"
            )
            
            logger.info("Registered mathematical resources")
            
        except Exception as e:
            logger.warning(f"Failed to register math resources: {e}")
    
    def get_function_stats(self) -> Dict[str, Any]:
        """Get function filtering statistics."""
        return self.function_filter.get_function_stats()

# Factory function for easy server creation
def create_math_server(config_file=None, **kwargs) -> ConfigurableMCPMathServer:
    """Create a configured math server instance.
    
    Args:
        config_file: Optional path to configuration file
        **kwargs: Additional configuration options
    
    Returns:
        ConfigurableMCPMathServer instance
    """
    if config_file:
        config = ServerConfig.from_file(config_file)
        # Apply any overrides
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
    else:
        config = ServerConfig(**kwargs)
    
    return ConfigurableMCPMathServer(config)