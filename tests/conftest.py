"""
Pytest configuration and fixtures for Bpod rig tests.

To run hardware tests:
>>> uv run pytest --runhardware

To run hardware tests with specific rig:
>>> uv run pytest --runhardware --port COM3
"""

import logging
from typing import Generator

import pytest
from bpod_core.bpod import Bpod

logger = logging.getLogger(__name__)


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--runhardware", action="store_true", default=False, help="run hardware tests"
    )
    parser.addoption(
        "--serial-number",
        action="store",
        default=None,
        help="Bpod rig serial number, fed to Bpod() if --runhardware is given",
    )
    parser.addoption(
        "--port",
        action="store",
        default=None,
        help="Bpod rig port, fed to Bpod() if --runhardware is given",
    )


def pytest_configure(config: pytest.Config):
    config.addinivalue_line("markers", "hardware: mark test as hardware to run")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    """Pytest hook to modify collected test items."""
    if config.getoption("--runhardware"):
        # --runhardware given in cli: do not skip hardware tests
        return

    # Add skip marker to hardware tests if --runhardware option not given
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


def emit_startup_message(message: str) -> None:
    """Write startup details to both terminal output and the logger."""
    print(message)
    logger.info(message)


@pytest.fixture(scope="session")
def bpod_device(request: pytest.FixtureRequest) -> Generator[Bpod, None, None]:
    """Fixture for providing a Bpod rig instance for tests."""
    bpod_instance = create_bpod_instance(request)
    logger.info(f"Successfully connected to Bpod rig in fixture: {bpod_instance}")
    yield bpod_instance
    bpod_instance.close()


@pytest.hookimpl()
def pytest_sessionstart(session: pytest.Session):
    """Pytest hook that runs before any tests are run."""
    # https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_sessionstart
    import datetime

    logger.info(f"Starting tests {datetime.datetime.now().isoformat()}")

    # Attempt to connect to the Bpod rig if --runhardware
    # option is given, and exit the tests if connection fails
    if session.config.getoption("--runhardware"):
        try:
            bpod_instance = create_bpod_instance(session)
            # Print some useful information about the connected rig
            emit_startup_message("Connected to Bpod rig:")
            emit_startup_message(f"  Serial Number: {bpod_instance.serial_number}")
            emit_startup_message(f"  Port: {bpod_instance.port}")
            emit_startup_message(
                f"  bpod_core.bpod.Bpod.version: {bpod_instance.version}"
            )
            bpod_instance.close()
        except Exception as _:
            pytest.exit("Connection to Bpod rig unsuccessful!")
