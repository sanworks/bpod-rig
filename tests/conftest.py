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


@pytest.fixture(scope="session")
def bpod_device(request: pytest.FixtureRequest) -> Generator[Bpod, None, None]:
    """Fixture for providing a Bpod rig instance for tests."""
    if not request.config.getoption("--runhardware"):
        # If not running hardware tests, skip fixture setup
        logger.info("Hardware tests not enabled; skipping Bpod device fixture setup.")
        return
    try:
        serial_number: str | None = request.config.getoption("--serial-number")
        serial_number = None if serial_number == "None" else serial_number
        port: str | None = request.config.getoption("--port")
        port = None if port == "None" else port

        bpod_instance = Bpod(serial_number=serial_number, port=port)
    except Exception as e:
        logger.error("Failed to connect to Bpod rig in fixture!", exc_info=e)
        pytest.exit("Connection to Bpod rig unsuccessful!")
    yield bpod_instance
    bpod_instance.close()
