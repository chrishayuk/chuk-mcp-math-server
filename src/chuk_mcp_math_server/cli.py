#!/usr/bin/env python3
# src/chuk_mcp_math_server/cli.py
"""
Command line interface for the MCP Math Server.
"""

import argparse
import json
import logging
import sys
from typing import Dict, Any

# Early logging configuration for stdio mode
# This must happen BEFORE any other imports to catch import-time logs
if "--transport" not in sys.argv and "stdio" not in sys.argv:
    # Default is stdio, so configure early if not explicitly http
    if "--verbose" not in sys.argv and "-v" not in sys.argv:
        logging.basicConfig(level=logging.WARNING, force=True)
        logging.getLogger("chuk_mcp_math").setLevel(logging.WARNING)
elif "--transport" in sys.argv:
    # Check if stdio is specified
    try:
        transport_idx = sys.argv.index("--transport")
        if transport_idx + 1 < len(sys.argv) and sys.argv[transport_idx + 1] == "stdio":
            if "--verbose" not in sys.argv and "-v" not in sys.argv:
                logging.basicConfig(level=logging.WARNING, force=True)
                logging.getLogger("chuk_mcp_math").setLevel(logging.WARNING)
    except (ValueError, IndexError):
        pass

from .math_config import MathServerConfig, load_math_configuration_from_sources
from .math_server import ConfigurableMCPMathServer

logger = logging.getLogger(__name__)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Configurable Chuk MCP Math Server - Highly Customizable Mathematical Function Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Transport settings
    transport_group = parser.add_argument_group("Transport Settings")
    transport_group.add_argument(
        "--transport",
        "-t",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport method to use (default: stdio)",
    )
    transport_group.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Port for HTTP transport (default: 8000)",
    )
    transport_group.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP transport (default: 0.0.0.0)"
    )

    # Feature toggles
    feature_group = parser.add_argument_group("Feature Control")
    feature_group.add_argument(
        "--disable-tools",
        action="store_true",
        help="Disable mathematical tool registration",
    )
    feature_group.add_argument(
        "--disable-prompts", action="store_true", help="Disable prompt registration"
    )
    feature_group.add_argument(
        "--disable-resources", action="store_true", help="Disable resource registration"
    )

    # Function filtering
    filter_group = parser.add_argument_group("Function Filtering")
    filter_group.add_argument(
        "--functions",
        nargs="+",
        help="Whitelist specific functions (e.g., --functions is_prime fibonacci)",
    )
    filter_group.add_argument(
        "--exclude-functions",
        nargs="+",
        help="Blacklist specific functions (e.g., --exclude-functions slow_function)",
    )
    filter_group.add_argument(
        "--domains",
        nargs="+",
        choices=["arithmetic", "number_theory", "trigonometry"],
        help="Whitelist mathematical domains",
    )
    filter_group.add_argument(
        "--exclude-domains",
        nargs="+",
        choices=["arithmetic", "number_theory", "trigonometry"],
        help="Blacklist mathematical domains",
    )
    filter_group.add_argument(
        "--categories",
        nargs="+",
        help="Whitelist function categories (e.g., --categories core primes)",
    )
    filter_group.add_argument(
        "--exclude-categories", nargs="+", help="Blacklist function categories"
    )

    # Performance settings
    perf_group = parser.add_argument_group("Performance Settings")
    perf_group.add_argument(
        "--cache-strategy",
        choices=["none", "memory", "smart"],
        default="smart",
        help="Caching strategy (default: smart)",
    )
    perf_group.add_argument(
        "--cache-size",
        type=int,
        default=1000,
        help="Cache size for mathematical functions (default: 1000)",
    )
    perf_group.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Computation timeout in seconds (default: 30.0)",
    )

    # Logging and debugging
    log_group = parser.add_argument_group("Logging")
    log_group.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose debug logging"
    )
    log_group.add_argument(
        "--quiet", "-q", action="store_true", help="Minimize logging output"
    )

    # Configuration file
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--config", "-c", help="Load configuration from file (YAML or JSON)"
    )
    config_group.add_argument(
        "--save-config", help="Save current configuration to file and exit"
    )
    config_group.add_argument(
        "--show-config", action="store_true", help="Show current configuration and exit"
    )

    return parser


def args_to_config_overrides(args) -> Dict[str, Any]:
    """Convert command line arguments to configuration overrides."""
    cli_overrides = {
        "transport": args.transport,
        "port": args.port,
        "host": args.host,
        "enable_tools": not args.disable_tools,
        "enable_prompts": not args.disable_prompts,
        "enable_resources": not args.disable_resources,
        "verbose": args.verbose,
        "quiet": args.quiet,
        "cache_strategy": args.cache_strategy,
        "cache_size": args.cache_size,
        "computation_timeout": args.timeout,
    }

    # Handle list arguments
    list_overrides = {}
    if args.functions:
        list_overrides["function_allowlist"] = args.functions
    if args.exclude_functions:
        list_overrides["function_denylist"] = args.exclude_functions
    if args.domains:
        list_overrides["domain_allowlist"] = args.domains
    if args.exclude_domains:
        list_overrides["domain_denylist"] = args.exclude_domains
    if args.categories:
        list_overrides["category_allowlist"] = args.categories
    if args.exclude_categories:
        list_overrides["category_denylist"] = args.exclude_categories

    # Handle log level
    if args.verbose:
        cli_overrides["log_level"] = "DEBUG"
    elif args.quiet:
        cli_overrides["log_level"] = "WARNING"

    # Merge with list overrides
    cli_overrides.update(list_overrides)

    # Filter out None values
    return {k: v for k, v in cli_overrides.items() if v is not None}


def check_dependencies():
    """Check and report on required dependencies."""
    # All dependencies are required and checked at import time
    # If we get here, they're all available
    return True


def run_server(config: MathServerConfig):
    """Run the server with the given configuration."""
    try:
        # Create and run server
        server = ConfigurableMCPMathServer(config)

        logger.info("✨ Configurable MCP Math Server starting...")
        logger.info(f"🎯 Transport: {config.transport}")
        if config.transport == "http":
            logger.info(f"🌐 Host: {config.host}:{config.port}")

        # Show filtering info
        stats = server.get_function_stats()
        if stats["filtering_active"]:
            logger.info(
                f"🔍 Function filtering active: {stats['total_filtered']}/{stats['total_available']} functions"
            )
        else:
            logger.info(f"📊 All {stats['total_available']} functions available")

        server.run()

    except KeyboardInterrupt:
        logger.info("🛑 Server interrupted by user")
    except Exception as e:
        logger.error(f"💥 Server failed: {e}")
        raise


def main():
    """Main entry point for the CLI."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Configure logging early for stdio mode to reduce noise
    # This happens before config loading to catch all import-time logs
    if args.transport == "stdio" and not args.verbose:
        # Set WARNING level for stdio to reduce noise
        logging.basicConfig(level=logging.WARNING, force=True)
        logging.getLogger("chuk_mcp_math").setLevel(logging.WARNING)
        logging.getLogger("chuk_mcp_math_server").setLevel(logging.WARNING)

    # Check dependencies first
    check_dependencies()

    try:
        # Load configuration
        cli_overrides = args_to_config_overrides(args)
        config = load_math_configuration_from_sources(
            config_file=args.config, cli_overrides=cli_overrides
        )

        # For stdio mode, default to WARNING level unless explicitly set
        if config.transport == "stdio" and not args.verbose and not args.quiet:
            config.log_level = "WARNING"

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
            print(json.dumps(config.model_dump(), indent=2))
            return

        # Run the server
        run_server(config)

    except Exception as e:
        logger.error(f"💥 CLI failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
