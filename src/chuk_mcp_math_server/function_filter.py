#!/usr/bin/env python3
# src/chuk_mcp_math_server/function_filter.py
"""
Function filtering system for controlling which mathematical functions are exposed.
"""

import logging
import inspect
from typing import Dict, Any, Optional, Protocol
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
    parameters: Dict[str, Any]

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
                # Try the main method first
                self._all_functions = self._load_from_math_library()
                
                # If that returns empty, try direct module access
                if len(self._all_functions) == 0:
                    logger.warning("get_mcp_functions() returned 0 functions, trying direct module access")
                    self._all_functions = self._load_functions_directly()
                    
            except Exception as e:
                logger.error(f"Error loading functions: {e}")
                self._all_functions = {}
                
        return self._all_functions
    
    def _load_from_math_library(self) -> Dict[str, Any]:
        """Load functions using the standard chuk_mcp_math interface."""
        try:
            from chuk_mcp_math import get_mcp_functions
            return get_mcp_functions()
        except ImportError as e:
            logger.error(f"Could not import chuk_mcp_math: {e}")
            return {}
    
    def _load_functions_directly(self) -> Dict[str, Any]:
        """Load functions directly from modules if get_mcp_functions fails."""
        functions = {}
        
        try:
            # Import the modules
            from chuk_mcp_math import arithmetic, number_theory
            
            # Get arithmetic functions
            for attr_name in dir(arithmetic):
                if self._is_valid_function(arithmetic, attr_name):
                    func = getattr(arithmetic, attr_name)
                    qualified_name = f"arithmetic::{attr_name}"
                    functions[qualified_name] = MockFunctionSpec(attr_name, "arithmetic", "core", func)
            
            # Get number theory functions  
            for attr_name in dir(number_theory):
                if self._is_valid_function(number_theory, attr_name):
                    func = getattr(number_theory, attr_name)
                    qualified_name = f"number_theory::{attr_name}"
                    functions[qualified_name] = MockFunctionSpec(attr_name, "number_theory", "primes", func)
            
            logger.info(f"Loaded {len(functions)} functions directly from modules")
            
        except Exception as e:
            logger.error(f"Error loading functions directly: {e}")
            
        return functions
    
    def _is_valid_function(self, module, attr_name: str) -> bool:
        """Check if an attribute is a valid function to expose."""
        if attr_name.startswith('_'):
            return False
        
        if attr_name in ['get_module_info', 'get_reorganized_modules', 'print_reorganized_status']:
            return False
        
        attr = getattr(module, attr_name)
        return callable(attr) and hasattr(attr, '__name__')
    
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
    
    def reset_cache(self):
        """Reset the function cache to force reloading."""
        self._all_functions = None
        self._filtered_functions = None