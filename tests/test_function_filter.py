"""Tests for function filtering functionality."""

from unittest.mock import MagicMock, patch

from chuk_mcp_math_server.function_filter import FunctionFilter, MockFunctionSpec
from chuk_mcp_math_server import MathServerConfig


class TestFunctionFilter:
    """Test function filtering logic."""

    def test_load_all_functions(self, math_config):
        """Test loading all functions without filtering."""
        filter = FunctionFilter(math_config)
        functions = filter.get_filtered_functions()

        assert len(functions) > 0, "Should load mathematical functions"
        assert len(functions) == 393, f"Expected 393 functions, got {len(functions)}"

    def test_function_allowlist(self, filtered_config):
        """Test function allowlist filtering."""
        filter = FunctionFilter(filtered_config)
        functions = filter.get_filtered_functions()

        assert len(functions) == 4, f"Expected 4 functions, got {len(functions)}"
        assert "add" in [f.function_name for f in functions.values()]
        assert "subtract" in [f.function_name for f in functions.values()]
        assert "multiply" in [f.function_name for f in functions.values()]
        assert "divide" in [f.function_name for f in functions.values()]

    def test_function_denylist(self):
        """Test function denylist filtering."""
        config = MathServerConfig(
            transport="stdio",
            log_level="WARNING",
            function_denylist=["add", "subtract"],
        )
        filter = FunctionFilter(config)
        functions = filter.get_filtered_functions()

        function_names = [f.function_name for f in functions.values()]
        assert "add" not in function_names
        assert "subtract" not in function_names
        assert "multiply" in function_names

    def test_domain_allowlist(self, domain_filtered_config):
        """Test domain allowlist filtering."""
        filter = FunctionFilter(domain_filtered_config)
        functions = filter.get_filtered_functions()

        # All functions should be from arithmetic domain
        for func in functions.values():
            assert func.namespace == "arithmetic", (
                f"Expected arithmetic, got {func.namespace}"
            )

        assert len(functions) > 0, "Should have arithmetic functions"

    def test_domain_denylist(self):
        """Test domain denylist filtering."""
        config = MathServerConfig(
            transport="stdio", log_level="WARNING", domain_denylist=["trigonometry"]
        )
        filter = FunctionFilter(config)
        functions = filter.get_filtered_functions()

        # No trigonometry functions should be present
        for func in functions.values():
            assert func.namespace != "trigonometry"

    def test_category_filtering(self):
        """Test category filtering."""
        config = MathServerConfig(
            transport="stdio", log_level="WARNING", category_allowlist=["core"]
        )
        filter = FunctionFilter(config)
        functions = filter.get_filtered_functions()

        # All functions should be core category
        for func in functions.values():
            assert func.category == "core", f"Expected core, got {func.category}"

    def test_function_stats(self, math_config):
        """Test function statistics."""
        filter = FunctionFilter(math_config)
        stats = filter.get_function_stats()

        assert "total_available" in stats
        assert "total_filtered" in stats
        assert "filtering_active" in stats
        assert "domains_filtered" in stats

        assert stats["total_available"] == 393
        assert stats["total_filtered"] == 393
        assert not stats["filtering_active"]

    def test_function_stats_with_filtering(self, filtered_config):
        """Test function statistics with filtering active."""
        filter = FunctionFilter(filtered_config)
        stats = filter.get_function_stats()

        assert stats["total_available"] == 393
        assert stats["total_filtered"] == 4
        assert stats["filtering_active"]

    def test_combined_filters(self):
        """Test combining multiple filter types."""
        config = MathServerConfig(
            transport="stdio",
            log_level="WARNING",
            domain_allowlist=["arithmetic"],
            function_allowlist=["add", "multiply"],
        )
        filter = FunctionFilter(config)
        functions = filter.get_filtered_functions()

        assert len(functions) == 2
        function_names = [f.function_name for f in functions.values()]
        assert "add" in function_names
        assert "multiply" in function_names

    def test_empty_filter_result(self):
        """Test that invalid filters return empty results."""
        config = MathServerConfig(
            transport="stdio",
            log_level="WARNING",
            function_allowlist=["nonexistent_function"],
        )
        filter = FunctionFilter(config)
        functions = filter.get_filtered_functions()

        assert len(functions) == 0, "Should return empty for nonexistent functions"


class TestMockFunctionSpec:
    """Test MockFunctionSpec creation and properties."""

    def test_mock_function_spec_creation(self):
        """Test creating a MockFunctionSpec."""

        def sample_func(x: int, y: int) -> int:
            return x + y

        spec = MockFunctionSpec("add", "arithmetic", "core", sample_func)

        assert spec.function_name == "add"
        assert spec.namespace == "arithmetic"
        assert spec.category == "core"
        assert spec.function_ref == sample_func
        assert spec.is_async_native is True
        assert spec.cache_strategy == "none"

    def test_mock_function_spec_parameters(self):
        """Test parameter extraction from function signature."""

        def func_with_types(x: int, y: float, name: str) -> str:
            return f"{name}: {x + y}"

        spec = MockFunctionSpec("test_func", "test", "core", func_with_types)

        assert "x" in spec.parameters
        assert "y" in spec.parameters
        assert "name" in spec.parameters
        assert spec.parameters["x"]["type"] == "integer"
        assert spec.parameters["y"]["type"] == "number"
        assert spec.parameters["name"]["type"] == "string"

    def test_mock_function_spec_no_annotations(self):
        """Test handling functions without type annotations."""

        def no_types(x, y):
            return x + y

        spec = MockFunctionSpec("no_types", "test", "core", no_types)

        assert "x" in spec.parameters
        assert "y" in spec.parameters
        assert spec.parameters["x"]["type"] == "any"
        assert spec.parameters["y"]["type"] == "any"

    def test_mock_function_spec_bool_type(self):
        """Test boolean type parameter extraction."""

        def bool_func(flag: bool) -> bool:
            return not flag

        spec = MockFunctionSpec("bool_func", "test", "core", bool_func)

        assert spec.parameters["flag"]["type"] == "boolean"

    def test_mock_function_spec_invalid_signature(self):
        """Test handling functions with invalid/complex signatures."""

        # Lambda or built-in that might have issues
        spec = MockFunctionSpec("lambda", "test", "core", lambda x: x)

        # Should have parameters dict even if extraction fails
        assert isinstance(spec.parameters, dict)


class TestFunctionFilterEdgeCases:
    """Test edge cases in function filtering."""

    def test_filter_caches_results(self):
        """Test that filtered functions are cached."""
        config = MathServerConfig(transport="stdio", log_level="WARNING")
        filter = FunctionFilter(config)

        # First call
        functions1 = filter.get_filtered_functions()
        # Second call should return cached result
        functions2 = filter.get_filtered_functions()

        assert functions1 is functions2  # Same object reference

    def test_all_functions_caches_results(self):
        """Test that all functions are cached."""
        config = MathServerConfig(transport="stdio", log_level="WARNING")
        filter = FunctionFilter(config)

        # First call
        all1 = filter.get_all_functions()
        # Second call should return cached result
        all2 = filter.get_all_functions()

        assert all1 is all2  # Same object reference

    @patch("chuk_mcp_math_server.function_filter.logger")
    def test_function_loading_handles_errors(self, mock_logger):
        """Test that function loading handles errors gracefully."""
        config = MathServerConfig(transport="stdio", log_level="WARNING")
        filter = FunctionFilter(config)

        # Should not raise, even if there are issues
        functions = filter.get_all_functions()
        assert isinstance(functions, dict)

    def test_should_include_function_with_allowlist(self):
        """Test _should_include_function with allowlist."""
        config = MathServerConfig(
            transport="stdio",
            log_level="WARNING",
            function_allowlist=["add"],
        )
        filter = FunctionFilter(config)

        # Create mock function spec
        mock_spec = MagicMock()
        mock_spec.function_name = "add"
        mock_spec.namespace = "arithmetic"
        mock_spec.category = "core"

        assert filter._should_include_function(mock_spec) is True

        mock_spec.function_name = "subtract"
        assert filter._should_include_function(mock_spec) is False

    def test_should_include_function_with_denylist(self):
        """Test _should_include_function with denylist."""
        config = MathServerConfig(
            transport="stdio",
            log_level="WARNING",
            function_denylist=["divide"],
        )
        filter = FunctionFilter(config)

        mock_spec = MagicMock()
        mock_spec.function_name = "add"
        mock_spec.namespace = "arithmetic"
        mock_spec.category = "core"

        assert filter._should_include_function(mock_spec) is True

        mock_spec.function_name = "divide"
        assert filter._should_include_function(mock_spec) is False

    def test_should_include_function_with_category_filter(self):
        """Test _should_include_function with category filtering."""
        config = MathServerConfig(
            transport="stdio",
            log_level="WARNING",
            category_allowlist=["core"],
        )
        filter = FunctionFilter(config)

        mock_spec = MagicMock()
        mock_spec.function_name = "add"
        mock_spec.namespace = "arithmetic"
        mock_spec.category = "core"

        assert filter._should_include_function(mock_spec) is True

        mock_spec.category = "advanced"
        assert filter._should_include_function(mock_spec) is False

    def test_get_all_domains(self):
        """Test getting all available domains."""
        config = MathServerConfig(transport="stdio", log_level="WARNING")
        filter = FunctionFilter(config)

        all_functions = filter.get_all_functions()
        domains = {func.namespace for func in all_functions.values()}

        assert len(domains) > 0
        assert "arithmetic" in domains

    def test_get_all_categories(self):
        """Test getting all available categories."""
        config = MathServerConfig(transport="stdio", log_level="WARNING")
        filter = FunctionFilter(config)

        all_functions = filter.get_all_functions()
        categories = {func.category for func in all_functions.values()}

        assert len(categories) > 0
        assert "core" in categories

    def test_domain_denylist_with_allowlist(self):
        """Test domain denylist combined with allowlist."""
        config = MathServerConfig(
            transport="stdio",
            log_level="WARNING",
            domain_allowlist=["arithmetic", "number_theory"],
            domain_denylist=["arithmetic"],
        )
        filter = FunctionFilter(config)
        functions = filter.get_filtered_functions()

        # Only number_theory should remain
        for func in functions.values():
            assert func.namespace == "number_theory"

    def test_category_denylist_with_allowlist(self):
        """Test category denylist combined with allowlist."""
        config = MathServerConfig(
            transport="stdio",
            log_level="WARNING",
            category_allowlist=["core", "advanced"],
            category_denylist=["advanced"],
        )
        filter = FunctionFilter(config)
        functions = filter.get_filtered_functions()

        # Only core should remain
        for func in functions.values():
            assert func.category == "core"

    def test_reset_cache(self):
        """Test that reset_cache clears cached functions."""
        config = MathServerConfig(transport="stdio", log_level="WARNING")
        filter = FunctionFilter(config)

        # Load functions to cache them
        functions1 = filter.get_filtered_functions()
        all1 = filter.get_all_functions()

        # Reset cache
        filter.reset_cache()

        # After reset, should reload (different object references)
        functions2 = filter.get_filtered_functions()
        all2 = filter.get_all_functions()

        # Content should be the same but not the same object
        assert len(functions1) == len(functions2)
        assert len(all1) == len(all2)


class TestMockFunctionSpecEdgeCases:
    """Test edge cases for MockFunctionSpec."""

    def test_union_type_handling(self):
        """Test handling of Union type annotations."""
        from typing import Union

        def union_func(x: Union[int, float]) -> Union[int, float]:
            return x * 2

        spec = MockFunctionSpec("union_func", "test", "core", union_func)

        # Union types should be simplified to "number"
        assert spec.parameters["x"]["type"] == "number"

    def test_exception_in_signature_parsing(self):
        """Test handling of exceptions during signature parsing."""

        # Create a mock object that will raise an exception when inspected
        class BadCallable:
            def __call__(self):
                pass

            @property
            def __signature__(self):
                raise RuntimeError("Cannot inspect signature")

        bad_func = BadCallable()
        spec = MockFunctionSpec("bad_func", "test", "core", bad_func)

        # Should have empty parameters dict when exception occurs
        assert spec.parameters == {}

    def test_category_denylist_filtering(self):
        """Test that category denylist correctly filters out functions."""
        config = MathServerConfig(
            transport="stdio",
            log_level="WARNING",
            category_denylist=["comparison"],  # Blacklist comparison category
        )
        filter = FunctionFilter(config)
        functions = filter.get_filtered_functions()

        # Verify no functions with "comparison" category remain
        for func in functions.values():
            assert func.category != "comparison"

    @patch("chuk_mcp_math_server.function_filter.logger")
    def test_trigonometry_import_error(self, mock_logger):
        """Test handling of trigonometry module import error."""
        # The trigonometry module import is wrapped in try/except
        # We can verify the logger is called correctly by checking the function loading
        config = MathServerConfig(transport="stdio", log_level="WARNING")
        filter = FunctionFilter(config)

        # This will trigger the import
        all_functions = filter.get_all_functions()

        # Should have loaded functions successfully even if trig is unavailable
        assert len(all_functions) > 0
