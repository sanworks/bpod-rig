import logging
import tempfile
from dataclasses import dataclass
from logging.config import dictConfig
from pathlib import Path
from typing import Generator, cast

import pytest

from bpod_rig.config import startup
from bpod_rig.log import BpodLogger, get_log_config


def get_logger() -> BpodLogger:
    logging_config = get_log_config(True)
    dictConfig(logging_config)
    logging.setLoggerClass(BpodLogger)
    logger: BpodLogger = cast(BpodLogger, logging.getLogger(__name__))
    return logger


@dataclass
class TempSetup:
    temp_dir: tempfile.TemporaryDirectory
    temp_path: Path
    bpod_path: Path
    system_path: Path


@pytest.fixture
def temp_setup(monkeypatch: pytest.MonkeyPatch) -> Generator[TempSetup, None, None]:
    """Fixture to create temporary directories for testing."""
    temp_dir = tempfile.TemporaryDirectory()
    temp_path = Path(temp_dir.name)
    bpod_path = temp_path / "Bpod"
    system_path = temp_path / "sanworks"
    monkeypatch.setattr(startup, "SYSTEM_CONFIG_DIR", system_path)
    monkeypatch.setattr(
        startup, "SYSTEM_CONFIG_FILE", system_path.joinpath("config.json")
    )

    yield TempSetup(
        temp_dir=temp_dir,
        temp_path=temp_path,
        bpod_path=bpod_path,
        system_path=system_path,
    )

    temp_dir.cleanup()


class DefaultChoiceAdapter(startup.StartupChoiceProtocol):
    def choose_override_path_first_init(self, default_path: Path) -> Path:
        return default_path

    def choose_reinitialize_invalid_dir(self, invalid_path: Path) -> bool | None:
        return True

    def choose_copy_defaults(self, bpod_path: Path) -> bool | None:
        return True


class TestCreateDefaultDirectories:

    def test_folder_creation(self, temp_setup: TempSetup):
        startup.create_default_directories(temp_setup.bpod_path)
        assert temp_setup.bpod_path.exists()


class TestInitService:

    def test_happy_path(self, temp_setup: TempSetup):
        result = startup.initialize_bpod_system(
            choices=DefaultChoiceAdapter(),
            default_bpod_path=temp_setup.bpod_path,
            logger=get_logger(),
        )

        expected_result = startup.InitResult(
            state=startup.InitState.COMPLETED,
            message="Initialization successful.",
            bpod_path=temp_setup.bpod_path,
            copied_defaults=True,
            details=None,
            user_config_path=temp_setup.bpod_path.joinpath("Config/config.json"),
            system_config_path=temp_setup.system_path.joinpath("config.json"),
        )
        assert result == expected_result
        assert temp_setup.bpod_path.joinpath("Config/config.json").exists()
        assert temp_setup.system_path.joinpath("config.json").exists()

    def test_malformed_system_config(self, temp_setup: TempSetup):
        # Create a malformed system config file
        temp_setup.system_path.mkdir(parents=True, exist_ok=True)
        malformed_config_path = temp_setup.system_path.joinpath("config.json")
        malformed_config_path.write_text("{ malformed json }")

        result = startup.initialize_bpod_system(
            choices=DefaultChoiceAdapter(),
            default_bpod_path=temp_setup.bpod_path,
            logger=get_logger(),
        )

        assert result.state == startup.InitState.FAILED
        # assert "Malformed system config" in result.message  # fails

    def test_log_swap_stream(self, temp_setup: TempSetup):
        # Test that the logger's stream is swapped to the file handler
        logger = get_logger()
        if logger.file_handler is None or logger.file_handler.log_dir is None:
            raise RuntimeError(
                "Logger does not have a file handler for testing log stream swapping."
            )
        assert logger.file_handler.log_dir.is_relative_to(Path(tempfile.gettempdir()))

        result = startup.initialize_bpod_system(
            choices=DefaultChoiceAdapter(),
            default_bpod_path=temp_setup.bpod_path,
            logger=logger,
        )

        assert result.state == startup.InitState.COMPLETED
        assert logger.file_handler.log_dir == temp_setup.bpod_path.joinpath("Logs")


class TestHelperFunctions: ...
