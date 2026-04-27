# List available commands
default:
    just --list

# Check formatting and types
check:
    -uv run ruff format --check .
    -uv run ruff check .
    -uv run pyright .

# Run tests
test:
    uv run pytest

# Automatically format files
format:
    uv run ruff format .
    uv run ruff check --fix .
