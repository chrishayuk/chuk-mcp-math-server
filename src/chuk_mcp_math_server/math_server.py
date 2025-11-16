#!/usr/bin/env python3
# src/chuk_mcp_math_server/math_server.py
"""
Mathematical MCP Server - using chuk-mcp-server framework.
"""

import json
import logging
from typing import Dict, Any

from chuk_mcp_server import ChukMCPServer

from .config import ServerConfig
from .function_filter import FunctionFilter

logger = logging.getLogger(__name__)


class ConfigurableMCPMathServer:
    """MCP Math Server with granular control over exposed mathematical functionality."""

    def __init__(self, config: ServerConfig):
        self.config = config

        # Configure logging early
        log_level = getattr(logging, config.log_level.upper())
        logging.getLogger().setLevel(log_level)

        # For stdio mode with WARNING or higher, silence noisy dependencies
        if config.transport == "stdio" and log_level >= logging.WARNING:
            logging.getLogger("chuk_mcp_math").setLevel(logging.WARNING)
            logging.getLogger("chuk_mcp_math_server.function_filter").setLevel(
                logging.WARNING
            )
            logging.getLogger("chuk_mcp_math_server.math_server").setLevel(
                logging.WARNING
            )
            logging.getLogger("chuk_mcp_math_server.cli").setLevel(logging.WARNING)

        self.function_filter = FunctionFilter(config)

        # Create the underlying chuk-mcp-server instance
        self.mcp_server = ChukMCPServer(
            name=config.server_name or "chuk-mcp-math-server"
        )

        # Register all tools and resources
        self._register_math_tools()
        self._register_math_resources()

        # Log math-specific initialization
        stats = self.function_filter.get_function_stats()
        logger.info(
            f"Math server initialized with {stats['total_filtered']}/{stats['total_available']} functions"
        )

    def _register_math_tools(self):
        """Register filtered mathematical functions as MCP tools."""

        # Get filtered functions
        filtered_functions = self.function_filter.get_filtered_functions()

        registered_count = 0
        for qualified_name, func_spec in filtered_functions.items():
            try:
                # Create a wrapper function that will be registered as a tool
                # We need to dynamically create the function with proper signature
                self._register_dynamic_tool(func_spec)
                registered_count += 1

            except Exception as e:
                logger.error(f"Failed to register tool {qualified_name}: {e}")

        logger.info(f"Registered {registered_count} mathematical tools")

    def _register_dynamic_tool(self, func_spec):
        """Dynamically register a mathematical function as a tool."""
        # Get the original function
        original_func = func_spec.function_ref

        if not original_func:
            logger.warning(f"No function reference for {func_spec.function_name}")
            return

        # Create description with domain and category info
        description = f"{func_spec.description} (Domain: {func_spec.namespace}, Category: {func_spec.category})"

        # Register the tool using the server's tool decorator
        # The function already has proper type hints and async handling from chuk_mcp_math
        self.mcp_server.tool(name=func_spec.function_name, description=description)(
            original_func
        )

    def _register_math_resources(self):
        """Register mathematical resources with configuration info."""
        # Create a reference to self for use in closures
        server = self

        # Available functions list resource
        @self.mcp_server.resource(  # type: ignore[misc]
            "math://available-functions",
            name="Available Functions",
            description="List of currently available mathematical functions after filtering",
            mime_type="application/json",
        )
        async def available_functions() -> str:
            filtered_functions = server.function_filter.get_filtered_functions()

            functions_by_domain: dict[str, list[dict[str, Any]]] = {}
            for func_spec in filtered_functions.values():
                domain = func_spec.namespace
                if domain not in functions_by_domain:
                    functions_by_domain[domain] = []

                functions_by_domain[domain].append(
                    {
                        "name": func_spec.function_name,
                        "description": func_spec.description,
                        "category": func_spec.category,
                        "async_native": func_spec.is_async_native,
                        "cached": func_spec.cache_strategy != "none",
                    }
                )

            return json.dumps(
                {
                    "total_functions": len(filtered_functions),
                    "functions_by_domain": functions_by_domain,
                    "filtering_applied": server.function_filter.get_function_stats()[
                        "filtering_active"
                    ],
                },
                indent=2,
            )

        # Function statistics resource
        @self.mcp_server.resource(  # type: ignore[misc]
            "math://function-stats",
            name="Function Statistics",
            description="Statistics about function filtering and availability",
            mime_type="application/json",
        )
        async def function_stats() -> str:
            stats = server.function_filter.get_function_stats()
            return json.dumps(stats, indent=2)

        # Server configuration resource
        @self.mcp_server.resource(  # type: ignore[misc]
            "math://server-config",
            name="Server Configuration",
            description="Current server configuration",
            mime_type="application/json",
        )
        async def server_config() -> str:
            return json.dumps(server.config.model_dump(), indent=2)

        logger.info("Registered mathematical resources")

    def get_function_stats(self) -> Dict[str, Any]:
        """Get function filtering statistics."""
        return self.function_filter.get_function_stats()

    def run(self):
        """Run the MCP server."""
        # Determine transport mode
        if self.config.transport == "http":
            logger.info(
                f"Starting HTTP server on {self.config.host}:{self.config.port}"
            )
            self.mcp_server.run(
                host=self.config.host,
                port=self.config.port,
                log_level=self.config.log_level.lower(),
            )
        else:
            logger.info("Starting stdio server")
            self.mcp_server.run(stdio=True, log_level=self.config.log_level.lower())


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
