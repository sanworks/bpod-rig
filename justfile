# List available commands
[private]
default:
    @just --list --unsorted

# Check formatting and types
check: _check-format _check-ruff _check-types

# Automatically format files
format:
    uv run ruff format .
    uv run ruff check --fix .

# Run tests, excluding hardware tests. Takes optional arguments to pass to pytest.
test *args:
    uv run pytest {{ args }}

# Run tests including tests requiring hardware.
test-hardware port="None" serial_number="None" *args:
    # Specify port OR serial number.
    uv run pytest --runhardware --port={{ port }} --serial-number={{ serial_number }} {{ args }}

# Subcommand to check code style with ruff (run by `check`)
_check-ruff:
    -uv run ruff check .

# Subcommand to check formatting (run by `check`)
_check-format:
    -uv run ruff format --check .

# Subcommand to check types (run by `check`)
_check-types:
    -uv run pyright .
