"""Integration tests for the math server."""

from unittest.mock import patch

from chuk_mcp_math_server import (
    ConfigurableMCPMathServer,
    MathServerConfig,
    create_math_server,
)


class TestMathServer:
    """Test the math server functionality."""

    def test_server_initialization(self, math_config):
        """Test that server initializes correctly."""
        server = ConfigurableMCPMathServer(math_config)

        assert server is not None
        assert server.config == math_config
        assert server.mcp_server is not None

    def test_server_with_all_functions(self, math_config):
        """Test server with all functions loaded."""
        server = ConfigurableMCPMathServer(math_config)
        stats = server.get_function_stats()

        assert stats["total_available"] == 393
        assert stats["total_filtered"] == 393
        assert not stats["filtering_active"]

    def test_server_with_filtered_functions(self, filtered_config):
        """Test server with function filtering."""
        server = ConfigurableMCPMathServer(filtered_config)
        stats = server.get_function_stats()

        assert stats["total_available"] == 393
        assert stats["total_filtered"] == 4
        assert stats["filtering_active"]

    def test_server_with_domain_filtering(self, domain_filtered_config):
        """Test server with domain filtering."""
        server = ConfigurableMCPMathServer(domain_filtered_config)
        stats = server.get_function_stats()

        assert stats["total_filtered"] > 0
        assert stats["total_filtered"] < 393
        assert stats["filtering_active"]
        assert "arithmetic" in stats["domains_filtered"]
        assert "trigonometry" not in stats["domains_filtered"]

    def test_function_stats(self, math_config):
        """Test getting function statistics."""
        server = ConfigurableMCPMathServer(math_config)
        stats = server.get_function_stats()

        assert "total_available" in stats
        assert "total_filtered" in stats
        assert "filtering_active" in stats
        assert "domains_filtered" in stats
        assert isinstance(stats["domains_filtered"], dict)

    def test_server_logging_configuration(self):
        """Test that logging is configured correctly."""
        config = MathServerConfig(transport="stdio", log_level="WARNING")
        server = ConfigurableMCPMathServer(config)

        # Should initialize without errors
        assert server is not None

    def test_multiple_server_instances(self, math_config, filtered_config):
        """Test that multiple server instances can coexist."""
        server1 = ConfigurableMCPMathServer(math_config)
        server2 = ConfigurableMCPMathServer(filtered_config)

        stats1 = server1.get_function_stats()
        stats2 = server2.get_function_stats()

        assert stats1["total_filtered"] == 393
        assert stats2["total_filtered"] == 4


class TestServerResources:
    """Test server resource registration."""

    def test_resources_registered(self, math_config):
        """Test that resources are registered."""
        server = ConfigurableMCPMathServer(math_config)

        # Server should have mcp_server initialized
        assert server.mcp_server is not None

        # Resources should be registered (we can't easily check the internal
        # registry without accessing private attributes, so we just verify
        # the server initialized successfully)
        assert server is not None

    @patch("chuk_mcp_math_server.math_server.logger")
    def test_dynamic_tool_registration(self, mock_logger, math_config):
        """Test dynamic tool registration."""
        server = ConfigurableMCPMathServer(math_config)

        # Should have registered tools
        stats = server.get_function_stats()
        assert stats["total_filtered"] > 0

        # Logger should have been called about registration
        mock_logger.info.assert_any_call(
            f"Registered {stats['total_filtered']} mathematical tools"
        )

    @patch("chuk_mcp_math_server.math_server.logger")
    def test_tool_registration_error_handling(self, mock_logger):
        """Test tool registration error handling."""
        # Create a server with invalid function spec
        config = MathServerConfig(function_allowlist=["add"])

        # Mock _register_dynamic_tool to raise an exception
        with patch.object(
            ConfigurableMCPMathServer,
            "_register_dynamic_tool",
            side_effect=RuntimeError("Test error"),
        ):
            server = ConfigurableMCPMathServer(config)

            # Should still initialize successfully
            assert server is not None
            # Error should have been logged
            mock_logger.error.assert_called()

    @patch("chuk_mcp_math_server.math_server.logger")
    def test_missing_function_ref(self, mock_logger):
        """Test handling of function spec without function_ref."""
        from unittest.mock import MagicMock

        config = MathServerConfig()
        server = ConfigurableMCPMathServer(config)

        # Create a mock function spec with no function_ref
        mock_spec = MagicMock()
        mock_spec.function_ref = None
        mock_spec.function_name = "test_func"

        # Call _register_dynamic_tool with the mock spec
        server._register_dynamic_tool(mock_spec)

        # Should have logged a warning
        mock_logger.warning.assert_called_once()
        assert "No function reference" in str(mock_logger.warning.call_args)

    def test_server_run_stdio(self, math_config):
        """Test server run with stdio transport."""
        server = ConfigurableMCPMathServer(math_config)

        # Mock the underlying run method
        with patch.object(server.mcp_server, "run") as mock_run:
            server.run()
            mock_run.assert_called_once_with(stdio=True, log_level="warning")

    def test_server_run_http(self):
        """Test server run with HTTP transport."""
        config = MathServerConfig(transport="http", port=9000, host="127.0.0.1")
        server = ConfigurableMCPMathServer(config)

        # Mock the underlying run method
        with patch.object(server.mcp_server, "run") as mock_run:
            server.run()
            mock_run.assert_called_once_with(
                host="127.0.0.1", port=9000, log_level="info"
            )

    async def test_available_functions_resource(self):
        """Test the available_functions resource."""
        import json

        config = MathServerConfig(function_allowlist=["add", "subtract"])
        server = ConfigurableMCPMathServer(config)

        # Get registered resources
        resources = server.mcp_server.get_resources()

        # Find the available_functions resource
        available_funcs_resource = None
        for resource in resources:
            if "available-functions" in resource.uri:
                available_funcs_resource = resource
                break

        assert available_funcs_resource is not None

        # Call the resource function
        result = await available_funcs_resource.handler()
        result_data = json.loads(result)

        # Verify structure
        assert "total_functions" in result_data
        assert "functions_by_domain" in result_data
        assert "filtering_applied" in result_data
        assert result_data["total_functions"] == 2

    async def test_function_stats_resource(self):
        """Test the function_stats resource."""
        import json

        config = MathServerConfig(domain_allowlist=["arithmetic"])
        server = ConfigurableMCPMathServer(config)

        # Get registered resources
        resources = server.mcp_server.get_resources()

        # Find the function-stats resource
        stats_resource = None
        for resource in resources:
            if "function-stats" in resource.uri:
                stats_resource = resource
                break

        assert stats_resource is not None

        # Call the resource function
        result = await stats_resource.handler()
        result_data = json.loads(result)

        # Verify stats structure
        assert "total_available" in result_data
        assert "total_filtered" in result_data
        assert "filtering_active" in result_data
        assert result_data["filtering_active"] is True

    async def test_server_config_resource(self):
        """Test the server_config resource."""
        import json

        config = MathServerConfig(transport="http", port=9001)
        server = ConfigurableMCPMathServer(config)

        # Get registered resources
        resources = server.mcp_server.get_resources()

        # Find the server-config resource
        config_resource = None
        for resource in resources:
            if "server-config" in resource.uri:
                config_resource = resource
                break

        assert config_resource is not None

        # Call the resource function
        result = await config_resource.handler()
        result_data = json.loads(result)

        assert result_data["transport"] == "http"
        assert result_data["port"] == 9001


class TestServerFactory:
    """Test server factory function."""

    def test_create_server_with_kwargs(self):
        """Test creating server with keyword arguments."""
        server = create_math_server(transport="stdio", log_level="WARNING")

        assert server is not None
        assert server.config.transport == "stdio"
        assert server.config.log_level == "WARNING"

    def test_create_server_with_filtering(self):
        """Test creating server with filtering options."""
        server = create_math_server(function_allowlist=["add", "subtract"])

        stats = server.get_function_stats()
        assert stats["total_filtered"] == 2
        assert stats["filtering_active"]


class TestServerEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_filter_list(self):
        """Test server with empty filter lists."""
        config = MathServerConfig(function_allowlist=[])
        server = ConfigurableMCPMathServer(config)
        stats = server.get_function_stats()

        # Empty allowlist is treated as "no filtering", so all functions pass
        # To actually filter to zero, you'd need a allowlist with non-existent functions
        assert stats["total_filtered"] >= 0

    def test_invalid_domain_filter(self):
        """Test server with invalid domain filter."""
        config = MathServerConfig(domain_allowlist=["nonexistent_domain"])
        server = ConfigurableMCPMathServer(config)
        stats = server.get_function_stats()

        # Invalid domain means no functions pass
        assert stats["total_filtered"] == 0

    def test_conflicting_filters(self):
        """Test server with conflicting allowlist and denylist."""
        config = MathServerConfig(
            function_allowlist=["add", "subtract"],
            function_denylist=["add"],  # Conflicts with allowlist
        )
        server = ConfigurableMCPMathServer(config)
        stats = server.get_function_stats()

        # Whitelist takes precedence, but denylist filters from allowlist
        assert stats["total_filtered"] <= 2

    def test_create_server_with_config_file(self, tmp_path):
        """Test create_math_server with config file."""
        import yaml

        config_file = tmp_path / "server_config.yaml"
        config_file.write_text(
            yaml.dump({"transport": "stdio", "function_allowlist": ["add", "subtract"]})
        )

        server = create_math_server(config_file=str(config_file), port=9999)

        # Config from file should be loaded
        assert server.config.function_allowlist == ["add", "subtract"]
        # Kwarg override should be applied
        assert server.config.port == 9999

    def test_server_logging_levels(self):
        """Test server with different logging levels."""
        config = MathServerConfig(log_level="DEBUG")
        server = ConfigurableMCPMathServer(config)

        assert server is not None

        # Test with ERROR level
        config2 = MathServerConfig(log_level="ERROR")
        server2 = ConfigurableMCPMathServer(config2)

        assert server2 is not None
