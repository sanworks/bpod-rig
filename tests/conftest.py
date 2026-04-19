"""
Pytest configuration and fixtures for Bpod rig tests.

To run hardware tests:
>>> uv run pytest --runhardware

To run hardware tests with specific rig:
>>> uv run pytest --runhardware --port COM3
"""

from typing import Generator

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


def create_bpod_instance(request: pytest.FixtureRequest | pytest.Session) -> Bpod:
    """Helper function to create a Bpod instance based on pytest options."""
    serial_number: str | None = request.config.getoption("--serial-number")
    serial_number = None if serial_number == "None" else serial_number
    port: str | None = request.config.getoption("--port")
    port = None if port == "None" else port

    return Bpod(serial_number=serial_number, port=port)


@pytest.fixture(scope="session")
def bpod_rig(request: pytest.FixtureRequest) -> Generator[Bpod, None, None]:
    """Fixture for providing a Bpod rig instance for tests."""
    bpod_instance = create_bpod_instance(
        request
    )  # Test connection and exit if unsuccessful
    yield bpod_instance

    # Cleanup: close the connection when fixture scope ends
    bpod_instance.close()


@pytest.hookimpl()
def pytest_sessionstart(session: pytest.Session):
    """Pytest hook that runs before any tests are run."""
    # https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_sessionstart
    # Attempt to connect to the Bpod rig if --runhardware
    # option is given, and exit the tests if connection fails
    if session.config.getoption("--runhardware"):
        try:
            bpod_instance = create_bpod_instance(session)
            print("Connected to Bpod rig.")
            print(f"\tSerial Number: {bpod_instance.serial_number}")
            print(f"\tPort: {bpod_instance.port}")
            print(f"\tFirmware Version: {bpod_instance.version}")
            bpod_instance.close()
        except Exception as _:
            pytest.exit("Connection to Bpod rig unsuccessful!")
