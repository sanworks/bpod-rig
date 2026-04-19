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
    parser.addoption(
        "--port", action="store", default=None, help="Bpod rig port"
    )


def pytest_configure(config: pytest.Config):
    config.addinivalue_line("markers", "hardware: mark test as hardware to run")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    """
    Pytest hook to modify collected test items.
    """
    if config.getoption("--runhardware"):
        # --runhardware given in cli: do not skip hardware tests
        return
    skip_hardware = pytest.mark.skip(reason="need --runhardware option to run")
    for item in items:
        if "hardware" in item.keywords:
            item.add_marker(skip_hardware)

@pytest.fixture(scope="session")
def bpod_rig(request: pytest.FixtureRequest):
    """
    Fixture for providing a Bpod rig instance for tests.
    """
    serial_number: str | None = request.config.getoption("--serial-number")
    serial_number = serial_number if serial_number is not "None" else None

    port: str | None = request.config.getoption("--port")
    port = port if port is not "None" else None

    rig = Bpod(serial_number=serial_number, port=port)
    yield rig
    rig.close()