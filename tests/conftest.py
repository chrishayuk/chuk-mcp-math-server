"""Pytest configuration and fixtures."""

import pytest
import logging
from chuk_mcp_math_server import ServerConfig, MathServerConfig


@pytest.fixture
def basic_config():
    """Create a basic server configuration."""
    return ServerConfig(transport="stdio", log_level="WARNING")


@pytest.fixture
def math_config():
    """Create a basic math server configuration."""
    return MathServerConfig(transport="stdio", log_level="WARNING")


@pytest.fixture
def filtered_config():
    """Create a configuration with function filtering."""
    return MathServerConfig(
        transport="stdio",
        log_level="WARNING",
        function_allowlist=["add", "subtract", "multiply", "divide"],
    )


@pytest.fixture
def domain_filtered_config():
    """Create a configuration with domain filtering."""
    return MathServerConfig(
        transport="stdio", log_level="WARNING", domain_allowlist=["arithmetic"]
    )


@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests."""
    # Suppress logs during tests unless verbose mode
    logging.getLogger("chuk_mcp_math").setLevel(logging.ERROR)
    logging.getLogger("chuk_mcp_math_server").setLevel(logging.ERROR)
    logging.getLogger("chuk_mcp_server").setLevel(logging.ERROR)
