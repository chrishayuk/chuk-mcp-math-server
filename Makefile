.PHONY: clean clean-pyc clean-build clean-test clean-all test run build publish publish-test help install dev-install lint format typecheck check info run-http

# Default target
help:
	@echo "Chuk MCP Math Server - Development Tools"
	@echo "========================================="
	@echo ""
	@echo "Available targets:"
	@echo "  clean        - Remove Python bytecode and basic artifacts"
	@echo "  clean-all    - Deep clean everything (pyc, build, test, cache)"
	@echo "  install      - Install package in current environment"
	@echo "  dev-install  - Install in dev mode with all dependencies"
	@echo "  lint         - Run ruff linter"
	@echo "  format       - Auto-format code with ruff"
	@echo "  typecheck    - Run mypy type checker"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage report"
	@echo "  check        - Run all checks (lint, typecheck, test-cov)"
	@echo "  run          - Run math server (stdio mode)"
	@echo "  run-http     - Run math server (HTTP mode on port 8000)"
	@echo "  build        - Build distribution packages"
	@echo "  publish      - Build and publish to PyPI"
	@echo "  publish-test - Build and publish to test PyPI"
	@echo "  info         - Show project information"
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
	@echo "Building project..."
	@if command -v uv >/dev/null 2>&1; then \
		uv build; \
	else \
		python -m build; \
	fi
	@echo "Build complete. Distributions are in the 'dist' folder."

# Publish to PyPI
publish: build
	@echo "Publishing package to PyPI..."
	@if [ ! -d "dist" ] || [ -z "$$(ls -A dist 2>/dev/null)" ]; then \
		echo "Error: No distribution files found. Run 'make build' first."; \
		exit 1; \
	fi
	@last_build=$$(ls -t dist/*.tar.gz dist/*.whl 2>/dev/null | head -n 2); \
	if [ -z "$$last_build" ]; then \
		echo "Error: No valid distribution files found."; \
		exit 1; \
	fi; \
	echo "Uploading: $$last_build"; \
	if command -v uv >/dev/null 2>&1; then \
		uv run twine upload $$last_build; \
	else \
		twine upload $$last_build; \
	fi
	@echo "Publish complete."

# Publish to Test PyPI
publish-test: build
	@echo "Publishing to test PyPI..."
	@last_build=$$(ls -t dist/*.tar.gz dist/*.whl 2>/dev/null | head -n 2); \
	if [ -z "$$last_build" ]; then \
		echo "Error: No valid distribution files found."; \
		exit 1; \
	fi; \
	echo "Uploading to test PyPI: $$last_build"; \
	if command -v uv >/dev/null 2>&1; then \
		uv run twine upload --repository testpypi $$last_build; \
	else \
		twine upload --repository testpypi $$last_build; \
	fi

# Show project info
info:
	@echo "Project Information:"
	@echo "==================="
	@if [ -f "pyproject.toml" ]; then \
		echo "Package: chuk-mcp-math-server"; \
		grep "^version" pyproject.toml || echo "Version: unknown"; \
		echo ""; \
		if command -v uv >/dev/null 2>&1; then \
			echo "UV version: $$(uv --version)"; \
		fi; \
		if command -v python >/dev/null 2>&1; then \
			echo "Python version: $$(python --version)"; \
		fi; \
	else \
		echo "No pyproject.toml found"; \
	fi
	@echo "Current directory: $$(pwd)"
	@echo ""
	@echo "Git status:"
	@git status --short 2>/dev/null || echo "Not a git repository"
