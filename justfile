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

# Run tests, excluding hardware tests
test ARGS=".":
    uv run pytest {{ ARGS }}

# Run all tests including tests requiring hardware
test-hardware port="None" serial_number="None":
    uv run pytest --runhardware --port={{ port }} --serial-number={{ serial_number }}

# Automatically format files
format:
    uv run ruff format .
    uv run ruff check --fix .
