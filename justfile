# List available commands
default:
    just --list

# Check formatting and types

check-ruff:
    -uv run ruff check .

check-format:
    -uv run ruff format --check .

check-types:
    -uv run pyright .

check: check-format check-ruff check-types

# Run tests
test:
    uv run pytest

# Automatically format files
format:
    uv run ruff format .
    uv run ruff check --fix .

build-doc:
    sphinx-build docs/source docs/build
