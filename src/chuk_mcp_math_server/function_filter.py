#!/usr/bin/env python3
# src/chuk_mcp_math_server/function_filter.py
"""
Function filtering system for controlling which mathematical functions are exposed.
"""

import inspect
import logging
from typing import Any, Optional, Protocol

from .config import ServerConfig

logger = logging.getLogger(__name__)


class FunctionSpec(Protocol):
    """Protocol for function specifications."""

    function_name: str
    namespace: str
    category: str
    description: str
    function_ref: Any
    is_async_native: bool
    cache_strategy: str
    parameters: dict[str, Any]


class MockFunctionSpec:
    """Mock function spec for direct module loading."""

    def __init__(self, name: str, namespace: str, category: str, func):
        self.function_name = name
        self.namespace = namespace
        self.category = category
        self.description = f"{name} function from {namespace}"
        self.function_ref = func
        self.is_async_native = True  # Assume async for chuk_mcp_math
        self.cache_strategy = "none"

        # Try to extract parameters from function signature
        try:
            sig = inspect.signature(func)
            self.parameters = {}
            for param_name, param in sig.parameters.items():
                if param.annotation != inspect.Parameter.empty:
                    param_type = (
                        str(param.annotation).replace("<class '", "").replace("'>", "")
                    )
                    if "Union" in param_type:
                        param_type = "number"  # Simplify Union types
                    elif "int" in param_type.lower():
                        param_type = "integer"
                    elif "float" in param_type.lower():
                        param_type = "number"
                    elif "bool" in param_type.lower():
                        param_type = "boolean"
                    elif "str" in param_type.lower():
                        param_type = "string"
                    self.parameters[param_name] = {"type": param_type}
                else:
                    self.parameters[param_name] = {"type": "any"}
        except Exception:
            self.parameters = {}


class FunctionFilter:
    """Filters mathematical functions based on configuration criteria."""

    def __init__(self, config: ServerConfig):
        self.config = config
        self._all_functions: Optional[dict[str, FunctionSpec]] = None
        self._filtered_functions: Optional[dict[str, FunctionSpec]] = None

    def get_all_functions(self) -> dict[str, FunctionSpec]:
        """Get all available mathematical functions."""
        if self._all_functions is None:
            self._all_functions = self._load_from_math_library()
        return self._all_functions

    def _load_from_math_library(self) -> dict[str, FunctionSpec]:
        """Load functions using the standard chuk_mcp_math interface."""
        # Import modules to register their functions
        # This is required because chuk_mcp_math doesn't auto-import to avoid circular imports
        from chuk_mcp_math import get_mcp_functions
        from chuk_mcp_math import number_theory  # noqa: F401
        from chuk_mcp_math.arithmetic import comparison, core  # noqa: F401

        try:
            # Import trigonometry functions if available
            from chuk_mcp_math import trigonometry  # noqa: F401

            logger.debug("Imported trigonometry module")
        except ImportError:
            logger.debug("Trigonometry module not available")

        # Get the registered functions
        functions = get_mcp_functions()
        logger.info(f"Loaded {len(functions)} functions from chuk_mcp_math")
        return functions  # type: ignore[no-any-return]

    def get_filtered_functions(self) -> dict[str, FunctionSpec]:
        """Get functions filtered according to configuration."""
        if self._filtered_functions is None:
            self._filtered_functions = self._apply_filters()
        return self._filtered_functions

    def _apply_filters(self) -> dict[str, FunctionSpec]:
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

        # Check function allowlist (if specified, only these are allowed)
        if self.config.function_allowlist:
            if func_spec.function_name not in self.config.function_allowlist:
                return False

        # Check function denylist
        if func_spec.function_name in self.config.function_denylist:
            return False

        # Check domain allowlist (if specified, only these domains are allowed)
        if self.config.domain_allowlist:
            if func_spec.namespace not in self.config.domain_allowlist:
                return False

        # Check domain denylist
        if func_spec.namespace in self.config.domain_denylist:
            return False

        # Check category allowlist (if specified, only these categories are allowed)
        if self.config.category_allowlist:
            if func_spec.category not in self.config.category_allowlist:
                return False

        # Check category denylist
        if func_spec.category in self.config.category_denylist:
            return False

        return True

    def get_function_stats(self) -> dict[str, Any]:
        """Get statistics about function filtering."""
        all_functions = self.get_all_functions()
        filtered_functions = self.get_filtered_functions()

        # Count by domain
        all_domains: dict[str, int] = {}
        filtered_domains: dict[str, int] = {}

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
                self.config.function_allowlist
                or self.config.function_denylist
                or self.config.domain_allowlist
                or self.config.domain_denylist
                or self.config.category_allowlist
                or self.config.category_denylist
            ),
        }

    def reset_cache(self):
        """Reset the function cache to force reloading."""
        self._all_functions = None
        self._filtered_functions = None
