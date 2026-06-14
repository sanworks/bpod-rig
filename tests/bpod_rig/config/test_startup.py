import logging
import tempfile
from logging.config import dictConfig
from pathlib import Path
from typing import cast

import pytest

from bpod_rig.config import startup
from bpod_rig.log import BpodLogger, get_log_config


def get_logger() -> BpodLogger:
    logging_config = get_log_config(True)
    dictConfig(logging_config)
    logging.setLoggerClass(BpodLogger)
    logger: BpodLogger = cast(BpodLogger, logging.getLogger(__name__))
    return logger


class DefaultChoiceAdapter(startup.StartupChoicePort):
    def choose_path_first_init(self, default_path: Path) -> Path:
        return default_path

    def choose_reinitialize_invalid_dir(self, invalid_path: Path) -> bool | None:
        return True

    def choose_copy_defaults(self, bpod_path: Path) -> bool | None:
        return True


class TestCreateDefaultDirectories:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.bpod_path = self.temp_path / "Bpod"

        yield  # test runs here

        self.temp_dir.cleanup()

    def test_folder_creation(self):
        startup.create_default_directories(self.bpod_path)
        assert self.bpod_path.exists()


class TestInitService:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, monkeypatch: pytest.MonkeyPatch):
        """Setup and teardown."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Set DEFAULT_BPOD_PATH and SYSTEM_CONFIG_DIR to temp paths for testing
        self.bpod_path = self.temp_path / "Bpod"
        self.system_path = self.temp_path / "sanworks"

        monkeypatch.setattr(startup, "SYSTEM_CONFIG_DIR", self.system_path)
        monkeypatch.setattr(
            startup, "SYSTEM_CONFIG_FILE", self.system_path.joinpath("config.json")
        )

        yield  # test runs here

        self.temp_dir.cleanup()

    def test_happy_path(self):
        result = startup.initialize_bpod_system(
            choices=DefaultChoiceAdapter(),
            default_bpod_path=self.bpod_path,
            logger=get_logger(),
        )

        expected_result = startup.InitResult(
            state=startup.InitState.COMPLETED,
            message="Initialization successful.",
            bpod_path=self.bpod_path,
            copied_defaults=True,
            details=None,
            user_config_path=self.bpod_path.joinpath("Config/config.json"),
            system_config_path=self.system_path.joinpath("config.json"),
        )
        assert result == expected_result
        assert self.bpod_path.joinpath("Config/config.json").exists()
        assert self.system_path.joinpath("config.json").exists()
