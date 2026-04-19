import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runhardware", action="store_true", default=False, help="run hardware tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "hardware: mark test as hardware to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runhardware"):
        # --runhardware given in cli: do not skip hardware tests
        return
    skip_hardware = pytest.mark.skip(reason="need --runhardware option to run")
    for item in items:
        if "hardware" in item.keywords:
            item.add_marker(skip_hardware)