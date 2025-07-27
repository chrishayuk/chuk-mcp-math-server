# 🧮 Chuk MCP Math Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](https://github.com/chuk-mcp/chuk-mcp-math-server)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-orange.svg)](https://github.com/chuk-mcp/chuk-mcp)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A highly configurable **Mathematical Computation Protocol (MCP) server** that provides comprehensive mathematical functions with flexible transport options and streaming capabilities.

## ✨ Features

### 🔢 Mathematical Capabilities
- **286 Mathematical Functions** across multiple domains
- **Number Theory**: Prime testing, factorization, GCD, LCM, sequences
- **Arithmetic**: Basic operations, advanced calculations, statistics
- **Real-time Computation**: Async processing with timeout support
- **Function Filtering**: Configurable whitelisting/blacklisting by domain or category

### 🚀 Transport & Streaming
- **Dual Transport**: STDIO and HTTP support
- **HTTP Streaming**: Server-Sent Events for intensive computations
- **WebSocket Ready**: Extensible for real-time applications
- **CORS Support**: Cross-origin requests enabled

### ⚙️ Configuration
- **CLI Configuration**: Comprehensive command-line options
- **File Configuration**: YAML and JSON config file support
- **Environment Variables**: Container-friendly configuration
- **Dynamic Filtering**: Runtime function filtering capabilities

### 🛡️ Production Ready
- **Health Monitoring**: Built-in health check endpoints
- **Error Handling**: Graceful failure management
- **Logging**: Configurable log levels and output
- **Rate Limiting**: Optional request throttling
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

#### STDIO Transport (MCP Standard)
```bash
# Start server with STDIO transport
uv run chuk-mcp-math-server

# Or with Python
python src/chuk_mcp_math_server/math_server.py
```

#### HTTP Transport
```bash
# Start HTTP server
uv run chuk-mcp-math-server --transport http --port 8000

# Server will be available at http://localhost:8000
```

### Example Client Usage

#### Test with Examples
```bash
# Test STDIO client
uv run examples/stdio_client_example.py

# Test HTTP client with streaming
uv run examples/http_client_example.py
```

#### Basic HTTP API Usage
```bash
# Check server status
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health

# Sample response:
# {
#   "server": "chuk-mcp-math-server",
#   "version": "0.1.0",
#   "functions_available": 286,
#   "transport": "http"
# }
```

## 📖 Documentation

### Available Functions

The server provides 286 mathematical functions across these domains:

| Domain | Functions | Examples |
|--------|-----------|----------|
| **Arithmetic** | Basic operations, statistics | `add`, `multiply`, `mean`, `variance` |
| **Number Theory** | Primes, factorization, sequences | `is_prime`, `next_prime`, `fibonacci`, `gcd` |
| **Advanced Math** | Complex calculations | `sqrt`, `power`, `factorial`, `combinations` |

### Configuration Options

#### Command Line
```bash
# Basic configuration
chuk-mcp-math-server --transport http --port 8080 --host 0.0.0.0

# Function filtering
chuk-mcp-math-server --domains arithmetic number_theory --functions is_prime add

# Performance tuning
chuk-mcp-math-server --cache-strategy smart --timeout 60 --max-concurrent 20

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
enable_cors: true
log_level: "INFO"

# Function filtering
domain_whitelist: ["arithmetic", "number_theory"]
function_blacklist: ["slow_function"]

# Performance
cache_strategy: "smart"
cache_size: 1000
computation_timeout: 30.0
max_concurrent_calls: 10
```

```bash
# Use configuration file
chuk-mcp-math-server --config config.yaml
```

#### Environment Variables
```bash
export MCP_MATH_TRANSPORT="http"
export MCP_MATH_PORT=8000
export MCP_MATH_LOG_LEVEL="DEBUG"
export MCP_MATH_DOMAIN_WHITELIST="arithmetic,number_theory"

chuk-mcp-math-server
```

### MCP Protocol Usage

#### Initialize Connection
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "clientInfo": {
      "name": "my-math-client",
      "version": "1.0.0"
    }
  }
}
```

#### List Available Tools
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

#### Call Mathematical Function
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "is_prime",
    "arguments": {
      "n": 97
    }
  }
}
```

## 🛠️ Development

### Project Structure
```
chuk-mcp-math-server/
├── src/chuk_mcp_math_server/
│   ├── __init__.py              # Package initialization
│   ├── _version.py              # Dynamic version management
│   ├── _cli.py                  # CLI utilities
│   └── math_server.py           # Main server implementation
├── examples/
│   ├── stdio_client_example.py  # STDIO client demo
│   └── http_client_example.py   # HTTP client demo
├── tests/                       # Test suite
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

### Development Setup
```bash
# Install development dependencies
uv sync --group dev

# Install with all optional features
pip install -e .[full]

# Run formatting
black src/ examples/
isort src/ examples/

# Run tests
pytest

# Version information
chuk-mcp-math-server-info
```

### Adding New Functions

1. Add mathematical functions to the `chuk-mcp-math` library
2. Functions are automatically discovered and registered
3. Use function filtering to control exposure

### Custom Configuration

```python
from chuk_mcp_math_server import ServerConfig, ConfigurableMCPMathServer

# Create custom configuration
config = ServerConfig(
    transport="http",
    port=9000,
    domain_whitelist=["arithmetic"],
    enable_cors=True,
    log_level="DEBUG"
)

# Start server
server = ConfigurableMCPMathServer(config)
await server.run()
```

## 🌐 HTTP API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/` | GET | Server status and information |
| `/health` | GET | Health check and function count |
| `/mcp` | POST | MCP protocol messages |

### HTTP Streaming

The server supports Server-Sent Events (SSE) for computationally intensive operations:

```javascript
// Request with streaming
fetch('/mcp', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream'
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/call',
    params: {
      name: 'fibonacci',
      arguments: { n: 1000 }
    }
  })
})
```

## 📊 Performance

### Benchmarks
- **Function Calls**: ~1000 ops/sec (simple arithmetic)
- **Prime Testing**: ~100 ops/sec (medium-sized numbers)
- **Memory Usage**: ~50MB baseline + computation overhead
- **Startup Time**: ~2 seconds (286 functions loaded)

### Optimization Tips
- Use `cache_strategy: "smart"` for repeated calculations
- Increase `max_concurrent_calls` for high-throughput scenarios
- Use function filtering to reduce memory footprint
- Enable HTTP streaming for long-running computations

## 🔧 Troubleshooting

### Common Issues

#### Server Won't Start
```bash
# Check dependencies
chuk-mcp-math-server-info

# Verify configuration
chuk-mcp-math-server --show-config

# Debug mode
chuk-mcp-math-server --verbose
```

#### Function Not Available
```bash
# List all functions
chuk-mcp-math-server --domains arithmetic --show-config

# Check filtering
chuk-mcp-math-server --functions is_prime add --show-config
```

#### HTTP Connection Issues
```bash
# Test server health
curl http://localhost:8000/health

# Check CORS settings
chuk-mcp-math-server --transport http --enable-cors
```

### Debug Information

```bash
# Get detailed system info
chuk-mcp-math-server-info --info

# Check version detection
python -c "import chuk_mcp_math_server; chuk_mcp_math_server.print_version_info()"
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

### Code Style
- Use `black` for code formatting
- Use `isort` for import sorting
- Follow PEP 8 guidelines
- Add type hints where appropriate

## 📋 Requirements

### Core Dependencies
- Python 3.11+
- `chuk-mcp >= 0.5`
- `chuk-mcp-math >= 0.1.0`
- `fastapi >= 0.116.1`
- `uvicorn >= 0.35.0`
- `httpx >= 0.28.1`
- `pyyaml >= 6.0.2`

### Optional Dependencies
- Development tools: `pytest`, `black`, `isort`, `mypy`
- All optional: `pip install chuk-mcp-math-server[full]`

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on the [Model Context Protocol (MCP)](https://github.com/chuk-mcp/chuk-mcp)
- Mathematical functions provided by [chuk-mcp-math](https://github.com/chuk-mcp/chuk-mcp-math)
- Inspired by the need for accessible mathematical computation services

## 🔗 Links

- **Documentation**: [GitHub Wiki](https://github.com/chuk-mcp/chuk-mcp-math-server/wiki)
- **Issues**: [GitHub Issues](https://github.com/chuk-mcp/chuk-mcp-math-server/issues)
- **MCP Protocol**: [Official MCP Docs](https://github.com/chuk-mcp/chuk-mcp)
- **Mathematical Functions**: [chuk-mcp-math](https://github.com/chuk-mcp/chuk-mcp-math)

---

**Made with ❤️ by the Chuk MCP Team**

*Bringing mathematical computation to the Model Context Protocol ecosystem*