"""
Pytest configuration and fixtures for Bpod rig tests.

To run hardware tests:
>>> uv run pytest --runhardware

To run hardware tests with specific rig:
>>> uv run pytest --runhardware --port COM3
"""

import pytest
from bpod_core.bpod import Bpod


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--runhardware", action="store_true", default=False, help="run hardware tests"
    )
    parser.addoption(
        "--serial-number", action="store", default=None, help="Bpod rig serial number"
    )
    parser.addoption("--port", action="store", default=None, help="Bpod rig port")


def pytest_configure(config: pytest.Config):
    config.addinivalue_line("markers", "hardware: mark test as hardware to run")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    """Pytest hook to modify collected test items."""
    if config.getoption("--runhardware"):
        # --runhardware given in cli: do not skip hardware tests
        return
    skip_hardware = pytest.mark.skip(reason="need --runhardware option to run")
    for item in items:
        if "hardware" in item.keywords:
            item.add_marker(skip_hardware)


@pytest.fixture(scope="session")
def bpod_rig(request: pytest.FixtureRequest) -> Bpod:
    """Fixture for providing a Bpod rig instance for tests."""
    serial_number: str | None = request.config.getoption("--serial-number")
    serial_number = None if serial_number == "None" else serial_number
    port: str | None = request.config.getoption("--port")
    port = None if port == "None" else port
    return Bpod(serial_number=None, port=port)


@pytest.hookimpl()
def pytest_sessionstart(session: pytest.Session):
    """Pytest hook that runs before any tests are run."""
    # https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_sessionstart
    # Attempt to connect to the Bpod rig if --runhardware
    # option is given, and exit the tests if connection fails
    if session.config.getoption("--runhardware"):
        try:
            bpod_instance = bpod_rig._fixture_function(session)
            print("Connected to Bpod rig.")
            print(f"\tSerial Number: {bpod_instance.serial_number}")
            print(f"\tPort: {bpod_instance.port}")
            print(f"\tFirmware Version: {bpod_instance.firmware_version}")
        except Exception as _:
            pytest.exit("Connection to Bpod rig unsuccessful!")
