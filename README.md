# 🧮 Chuk MCP Math Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](https://github.com/chuk-mcp/chuk-mcp-math-server)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-orange.svg)](https://github.com/chuk-mcp/chuk-mcp)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Powered by chuk-mcp-server](https://img.shields.io/badge/powered%20by-chuk--mcp--server-blue)](https://github.com/chrishayuk/chuk-mcp-server)

A highly configurable **Mathematical Computation Protocol (MCP) server** that provides comprehensive mathematical functions with flexible transport options. Built on the high-performance [chuk-mcp-server](https://github.com/chrishayuk/chuk-mcp-server) framework.

## ⚡ Performance

- **36,000+ RPS** peak throughput (inherited from chuk-mcp-server)
- **Sub-3ms latency** per tool call
- **393 Mathematical Functions** available
- **Zero-config startup** - works out of the box

## ✨ Features

### 🔢 Mathematical Capabilities
- **393 Mathematical Functions** across multiple domains
- **Number Theory**: Prime testing, factorization, GCD, LCM, sequences (71 functions)
- **Arithmetic**: Basic operations, advanced calculations, statistics (322 functions)
- **Trigonometry**: Comprehensive trigonometric operations (71 functions)
- **Real-time Computation**: Async processing with proper error handling
- **Function Filtering**: Configurable allowlists and denylists by domain, category, or function

### 🚀 Transport & Architecture
- **Dual Transport**: STDIO (Claude Desktop) and HTTP support
- **High Performance**: Built on chuk-mcp-server framework
- **Auto-detection**: Automatically selects optimal transport mode
- **Production Ready**: 36,000+ RPS, <3ms latency
- **Type Safe**: Automatic schema generation from Python type hints

### ⚙️ Configuration
- **CLI Configuration**: Comprehensive command-line options
- **File Configuration**: YAML and JSON config file support
- **Environment Variables**: Container-friendly configuration
- **Dynamic Filtering**: Runtime function filtering with allowlists and denylists
- **Granular Control**: Filter by function, domain, or category

### 🛡️ Production Features
- **Zero Configuration**: Works out of the box with sensible defaults
- **High Test Coverage**: 97% code coverage with 114 comprehensive tests
- **Type Safe**: 100% type-checked with mypy, fully Pydantic-native
- **Error Handling**: Graceful failure management
- **Logging**: Configurable log levels and output
- **MCP Resources**: Built-in resources for function discovery and stats
- **Timeout Management**: Configurable computation timeouts

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/chuk-mcp/chuk-mcp-math-server.git
cd chuk-mcp-math-server

# Install dependencies
uv sync
# or
pip install -e .
```

### Basic Usage

#### STDIO Transport (Claude Desktop)
```bash
# Start server with STDIO transport (default)
uv run chuk-mcp-math-server

# Starts immediately with all 393 functions available
```

#### HTTP Transport (Web APIs)
```bash
# Start HTTP server
uv run chuk-mcp-math-server --transport http --port 8000

# Server will be available at http://localhost:8000
```

### Claude Desktop Integration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "math": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/chuk-mcp-math-server",
        "run",
        "chuk-mcp-math-server"
      ]
    }
  }
}
```

**Important:** Use absolute paths, not relative or `~` paths.

Restart Claude Desktop and ask: "Can you check if 97 is prime?" - Claude will use the math server!

### Example HTTP API Usage

```bash
# Test the server
curl http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'

# Call a mathematical function
curl http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "is_prime",
      "arguments": {"n": 97}
    }
  }'
```

## 📖 Documentation

### Available Functions

The server provides **393 mathematical functions** across these domains:

| Domain | Functions | Examples |
|--------|-----------|----------|
| **Arithmetic** (322) | Basic operations, comparisons, rounding, modular arithmetic | `add`, `multiply`, `modulo`, `gcd`, `lcm` |
| **Trigonometry** (71) | Trig functions, conversions, identities | `sin`, `cos`, `tan`, `radians`, `degrees` |
| **Number Theory** | Primes, sequences, special numbers | `is_prime`, `fibonacci`, `factorial`, `divisors` |

### Function Filtering

Control which functions are exposed:

```bash
# Only expose specific functions
chuk-mcp-math-server --functions add subtract multiply divide

# Expose only arithmetic domain
chuk-mcp-math-server --domains arithmetic

# Exclude specific functions
chuk-mcp-math-server --exclude-functions slow_function

# Combine filters
chuk-mcp-math-server --domains arithmetic number_theory --categories core primes
```

### Configuration Options

#### Command Line
```bash
# Basic configuration
chuk-mcp-math-server --transport http --port 8080 --host 0.0.0.0

# Function filtering
chuk-mcp-math-server --domains arithmetic --functions is_prime add

# Performance tuning
chuk-mcp-math-server --cache-strategy smart --timeout 60

# Logging
chuk-mcp-math-server --verbose  # Debug logging
chuk-mcp-math-server --quiet    # Minimal logging
```

#### Configuration File
```yaml
# config.yaml
transport: "http"
port: 8000
host: "0.0.0.0"
log_level: "INFO"

# Function filtering (allowlist: only these are enabled, denylist: these are excluded)
domain_allowlist: ["arithmetic", "number_theory"]
function_allowlist: ["is_prime", "fibonacci", "add", "multiply"]
function_denylist: ["deprecated_function"]  # Exclude specific functions

# Performance
cache_strategy: "smart"
cache_size: 1000
computation_timeout: 30.0
max_concurrent_calls: 10
```

```bash
# Use configuration file
chuk-mcp-math-server --config config.yaml

# Save current config
chuk-mcp-math-server --domains arithmetic --save-config my-config.yaml

# Show current config
chuk-mcp-math-server --show-config
```

### MCP Resources

The server provides built-in resources for introspection:

```bash
# List available functions (via MCP resource)
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/read",
  "params": {
    "uri": "math://available-functions"
  }
}

# Get function statistics
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/read",
  "params": {
    "uri": "math://function-stats"
  }
}

# Get server configuration
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resources/read",
  "params": {
    "uri": "math://server-config"
  }
}
```

## 🛠️ Development

### Project Structure
```
chuk-mcp-math-server/
├── src/chuk_mcp_math_server/
│   ├── __init__.py              # Package initialization
│   ├── cli.py                   # CLI implementation
│   ├── config.py                # Base configuration (Pydantic)
│   ├── math_config.py           # Math-specific configuration
│   ├── function_filter.py       # Function filtering logic
│   └── math_server.py           # Main server (uses chuk-mcp-server)
├── tests/                       # Test suite (97% coverage, 114 tests)
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

### Development Setup
```bash
# Install development dependencies
uv sync --group dev

# Run all checks (format, lint, typecheck, tests)
make check

# Run tests with coverage
make test-cov

# Run type checking
make typecheck

# Format code
make format

# Run with verbose logging
uv run chuk-mcp-math-server --verbose
```

### Custom Server
```python
from chuk_mcp_math_server import create_math_server

# Create server with custom configuration
server = create_math_server(
    transport="http",
    port=9000,
    domain_allowlist=["arithmetic"],  # Only arithmetic functions
    function_denylist=["deprecated_func"],  # Exclude specific functions
    log_level="DEBUG"
)

# Run the server
server.run()
```

## 📊 Performance

### Benchmarks
- **Peak Throughput**: 36,000+ requests/second
- **Average Latency**: <3ms per tool call
- **Startup Time**: ~2 seconds (393 functions loaded)
- **Memory Usage**: ~50MB baseline
- **Success Rate**: 100% under load testing

### Performance comes from:
- **chuk-mcp-server framework**: High-performance MCP implementation
- **Async operations**: Non-blocking I/O for all function calls
- **Type safety**: Automatic schema validation with zero overhead
- **Optimized registry**: Fast function lookup and execution

### Optimization Tips
- Use function filtering to reduce memory footprint
- Enable caching for repeated calculations (`--cache-strategy smart`)
- Use HTTP transport for web APIs, STDIO for local/Claude Desktop
- Adjust `--max-concurrent-calls` for high-throughput scenarios

## 🔧 Troubleshooting

### Common Issues

#### Server Won't Start
```bash
# Verify installation
python -c "import chuk_mcp_math_server; print(chuk_mcp_math_server.__version__)"

# Verify configuration
chuk-mcp-math-server --show-config

# Debug mode
chuk-mcp-math-server --verbose
```

#### Functions Not Loading
```bash
# Check if chuk-mcp-math is installed
python -c "import chuk_mcp_math; print(chuk_mcp_math.__version__)"

# Verify function count
chuk-mcp-math-server --show-config | grep total_filtered
```

#### Claude Desktop Not Showing Tools
1. Use **absolute paths** in claude_desktop_config.json (not `~` or relative)
2. Test manually: `echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | uv run chuk-mcp-math-server`
3. Restart Claude Desktop after config changes
4. Check Claude Desktop logs (Help → Show Logs)

#### HTTP Connection Issues
```bash
# Test server health
curl http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## 🤝 Contributing

We welcome contributions! Here's how to help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Ensure tests pass (`pytest`)
6. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Maintain 100% type safety with mypy and Pydantic
- Add type hints where appropriate
- Update documentation for new features
- Keep the README up to date
- Aim for high test coverage (currently 97%)

## 📋 Requirements

### Core Dependencies
- Python 3.11+
- `chuk-mcp-server >= 0.6` (provides high-performance MCP framework)
- `chuk-mcp-math >= 0.1.0` (provides mathematical functions)
- `pyyaml >= 6.0.2` (for YAML configuration)

### What's Included via chuk-mcp-server
- High-performance HTTP/STDIO transport
- Automatic type inference and validation
- Built-in logging and error handling
- Zero-config startup capability
- Production-grade performance (36K+ RPS)

### Optional Dependencies
- Development tools: `pytest`, `pytest-asyncio`
- All optional: `pip install -e .[dev]`

## 🏗️ Architecture

Built on **chuk-mcp-server** framework:
- **chuk-mcp-server**: High-performance MCP server framework (36K+ RPS)
- **chuk-mcp-math**: Mathematical function library (393 functions)
- **This server**: Bridges the two with filtering and configuration

The refactored architecture is simpler and more performant:
- Removed custom base server implementation
- Uses chuk-mcp-server's decorator-based API
- Maintains all filtering and configuration features
- Gains automatic performance optimization

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on [chuk-mcp-server](https://github.com/chrishayuk/chuk-mcp-server) - High-performance MCP framework
- Mathematical functions from [chuk-mcp-math](https://github.com/chuk-mcp/chuk-mcp-math)
- Follows the [Model Context Protocol](https://modelcontextprotocol.io) specification

## 🔗 Links

- **chuk-mcp-server**: [GitHub](https://github.com/chrishayuk/chuk-mcp-server) | [Docs](https://github.com/chrishayuk/chuk-mcp-server#readme)
- **chuk-mcp-math**: [GitHub](https://github.com/chuk-mcp/chuk-mcp-math)
- **MCP Protocol**: [Official Specification](https://modelcontextprotocol.io)
- **Issues**: [GitHub Issues](https://github.com/chuk-mcp/chuk-mcp-math-server/issues)

---

**Made with ❤️ by the Chuk MCP Team**

*High-performance mathematical computation for the Model Context Protocol ecosystem*
