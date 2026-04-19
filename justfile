# List available commands
default:
    just --list

# Check formatting and types
check:
    uv run ruff format --check .
    uv run ruff check .
    uv run pyright .

# Run tests, excluding hardware tests
test ARGS=".":
    uv run pytest {{ ARGS }}

# Run all tests including tests requiring hardware
test-hardware serial_number="None" port="None":
    uv run pytest --runhardware --serial-number {{ serial_number }} --port {{ port }}

# Automatically format files
format:
    uv run ruff format .
    uv run ruff check --fix .
