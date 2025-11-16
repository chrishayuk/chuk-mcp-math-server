.PHONY: clean clean-pyc clean-build clean-test clean-all test run build publish help install dev-install

# Default target
help:
	@echo "Chuk MCP Math Server - Development Tools"
	@echo "========================================="
	@echo ""
	@echo "Available targets:"
	@echo "  clean        - Remove Python bytecode and basic artifacts"
	@echo "  clean-all    - Deep clean everything"
	@echo "  install      - Install package"
	@echo "  dev-install  - Install in dev mode with dependencies"
	@echo "  lint         - Run ruff linter"
	@echo "  format       - Auto-format code with ruff"
	@echo "  typecheck    - Run mypy type checker"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  check        - Run all checks (lint, typecheck, test-cov)"
	@echo "  run          - Run math server (stdio mode)"
	@echo "  run-http     - Run math server (HTTP mode)"
	@echo "  build        - Build the project"
	@echo ""

# Clean targets
clean: clean-pyc clean-build

clean-pyc:
	@find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

clean-build:
	@rm -rf build/ dist/ *.egg-info 2>/dev/null || true

clean-test:
	@rm -rf .pytest_cache/ .coverage htmlcov/ 2>/dev/null || true

clean-all: clean-pyc clean-build clean-test
	@rm -rf .mypy_cache/ .ruff_cache/ .venv/ 2>/dev/null || true

# Install targets
install:
	pip install .

dev-install:
	@if command -v uv >/dev/null 2>&1; then \
		uv sync; \
		uv pip install pytest pytest-asyncio pytest-cov ruff mypy; \
	else \
		pip install -e "."; \
		pip install pytest pytest-asyncio pytest-cov ruff mypy; \
	fi

# Test targets
test:
	@if command -v uv >/dev/null 2>&1; then \
		uv run pytest; \
	else \
		pytest; \
	fi

test-cov:
	@if command -v uv >/dev/null 2>&1; then \
		uv run pytest --cov=src/chuk_mcp_math_server --cov-report=term-missing --cov-report=xml -v; \
	else \
		pytest --cov=src/chuk_mcp_math_server --cov-report=term-missing --cov-report=xml -v; \
	fi

# Code quality
lint:
	@if command -v uv >/dev/null 2>&1; then \
		uv run ruff check .; \
		uv run ruff format --check .; \
	else \
		ruff check .; \
		ruff format --check .; \
	fi

format:
	@if command -v uv >/dev/null 2>&1; then \
		uv run ruff format .; \
		uv run ruff check --fix .; \
	else \
		ruff format .; \
		ruff check --fix .; \
	fi

typecheck:
	@if command -v uv >/dev/null 2>&1; then \
		uv run mypy src/chuk_mcp_math_server || true; \
	else \
		mypy src/chuk_mcp_math_server || true; \
	fi

# Combined checks
check: lint typecheck test-cov
	@echo "✅ All checks passed!"

# Run targets
run:
	@if command -v uv >/dev/null 2>&1; then \
		uv run chuk-mcp-math-server; \
	else \
		python -m chuk_mcp_math_server.cli; \
	fi

run-http:
	@if command -v uv >/dev/null 2>&1; then \
		uv run chuk-mcp-math-server --transport http --port 8000; \
	else \
		python -m chuk_mcp_math_server.cli --transport http --port 8000; \
	fi

# Build
build: clean-build
	@if command -v uv >/dev/null 2>&1; then \
		uv build; \
	else \
		python -m build; \
	fi
