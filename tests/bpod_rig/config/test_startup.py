import logging
import tempfile
from collections.abc import Generator
from dataclasses import dataclass
from logging.config import dictConfig
from pathlib import Path
from typing import cast

import pytest

from bpod_rig.config import startup, system_settings
from bpod_rig.log import BpodLogger, get_log_config


def get_logger() -> BpodLogger:
    logging_config = get_log_config(debug=True)
    dictConfig(logging_config)
    logging.setLoggerClass(BpodLogger)
    logger: BpodLogger = cast("BpodLogger", logging.getLogger(__name__))
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


@dataclass
class ConfigurableChoiceAdapter(startup.StartupChoiceProtocol):
    """Adapter to provide configurable choices for testing purposes.

    The default values should always lead to successful initialization.

    Example usage:

        adapter = ConfigurableChoiceAdapter(
            override_path=Path("/custom/path"),
            )
    """

    override_path: Path | None = None
    reinitialize_system_config: bool = True
    reinitialize: bool = True
    copy_defaults: bool = True

    def choose_override_path_first_init(self, default_path: Path) -> Path:
        if self.override_path is not None:
            return self.override_path
        return default_path

    def choose_reinitialize_invalid_system_config(
        self, invalid_path: Path
    ) -> bool | None:
        return self.reinitialize_system_config

    def choose_reinitialize_invalid_dir(self, invalid_path: Path) -> bool | None:
        return self.reinitialize

    def choose_copy_defaults(self, bpod_path: Path) -> bool | None:
        return self.copy_defaults


class TestCreateDefaultDirectories:
    def test_folder_creation(self, temp_setup: TempSetup):
        startup.create_default_directories(temp_setup.bpod_path)
        assert temp_setup.bpod_path.exists()
        assert temp_setup.bpod_path.joinpath("Config").exists()
        assert temp_setup.bpod_path.joinpath("Logs").exists()
        assert temp_setup.bpod_path.joinpath("Protocols").exists()
        assert temp_setup.bpod_path.joinpath("Data").exists()


class TestInitializeBpodSystem:
    def test_happy_path(self, temp_setup: TempSetup):
        result = startup.initialize_bpod_system(
            choices=ConfigurableChoiceAdapter(),
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

    def test_malformed_system_config_overridden(self, temp_setup: TempSetup):
        # Create a malformed system config file
        temp_setup.system_path.mkdir(parents=True, exist_ok=True)
        malformed_config_path = temp_setup.system_path.joinpath("config.json")
        malformed_config_path.write_text("{ malformed json }")
        result = startup.initialize_bpod_system(
            choices=ConfigurableChoiceAdapter(),
            default_bpod_path=temp_setup.bpod_path,
            logger=get_logger(),
        )

        assert result.state == startup.InitState.COMPLETED

    def test_malformed_system_config_not_overridden(self, temp_setup: TempSetup):
        # Create a malformed system config file
        temp_setup.system_path.mkdir(parents=True, exist_ok=True)
        malformed_config_path = temp_setup.system_path.joinpath("config.json")
        malformed_config_path.write_text("{ malformed json }")
        result = startup.initialize_bpod_system(
            choices=ConfigurableChoiceAdapter(reinitialize_system_config=False),
            default_bpod_path=temp_setup.bpod_path,
            logger=get_logger(),
        )

        assert result.state == startup.InitState.INITIALIZED_INVALID

    def test_choose_override_path_first_init(self, temp_setup: TempSetup):
        # Provide a custom override path for the first initialization
        custom_path = temp_setup.temp_path / "CustomBpod"
        result = startup.initialize_bpod_system(
            choices=ConfigurableChoiceAdapter(override_path=custom_path),
            default_bpod_path=temp_setup.bpod_path,
            logger=get_logger(),
        )

        assert result.state == startup.InitState.COMPLETED
        assert result.bpod_path == custom_path
        assert custom_path.exists()

    def test_choose_reinitialize_invalid_dir(self, temp_setup: TempSetup):
        # Create an invalid Bpod directory (e.g., missing required subdirectories)
        invalid_bpod_path = temp_setup.temp_path / "InvalidBpod"
        invalid_bpod_path.mkdir(parents=True, exist_ok=True)

        system_paths = system_settings.BpodDir.create(base_dir=invalid_bpod_path)
        temp_setup.system_path.mkdir(parents=True, exist_ok=True)
        startup._initialize_system_config_dir(
            choices=ConfigurableChoiceAdapter(),
            bpod_path=invalid_bpod_path,
            logger=get_logger(),
        )
        temp_setup.system_path.joinpath("config.json").write_text(
            system_settings.SystemSettings.create(system_paths).model_dump_json()
        )
        invalid_bpod_path.joinpath("Logs").rmdir()
        assert startup.check_system_is_initialized()
        assert not system_paths.verify()

        # The actual test
        result = startup.initialize_bpod_system(
            choices=ConfigurableChoiceAdapter(reinitialize=False),
            default_bpod_path=invalid_bpod_path,
            logger=get_logger(),
        )

        assert result.state == startup.InitState.INITIALIZED_INVALID, result

        result = startup.initialize_bpod_system(
            choices=ConfigurableChoiceAdapter(reinitialize=True),
            default_bpod_path=invalid_bpod_path,
            logger=get_logger(),
        )

        assert result.state == startup.InitState.COMPLETED
        assert result.bpod_path == invalid_bpod_path
        # Check that the required subdirectories have been created
        assert (invalid_bpod_path / "Logs").exists()
        assert (invalid_bpod_path / "Protocols").exists()
        assert (invalid_bpod_path / "Data").exists()

    def test_log_swap_stream(self, temp_setup: TempSetup):
        # Test that the logger's stream is swapped to the Bpod folder
        logger = get_logger()
        if logger.file_handler is None or logger.file_handler.log_dir is None:
            raise RuntimeError(
                "Logger does not have a file handler for testing log stream swapping."
            )
        assert logger.file_handler.log_dir.is_relative_to(Path(tempfile.gettempdir()))

        result = startup.initialize_bpod_system(
            choices=ConfigurableChoiceAdapter(),
            default_bpod_path=temp_setup.bpod_path,
            logger=logger,
        )

        assert result.state == startup.InitState.COMPLETED
        assert logger.file_handler.log_dir == temp_setup.bpod_path.joinpath("Logs")

    def test_existing_valid_system_config(self, temp_setup: TempSetup):
        # Create a valid system config file
        result = startup.initialize_bpod_system(
            choices=ConfigurableChoiceAdapter(),
            default_bpod_path=temp_setup.bpod_path,
            logger=get_logger(),
        )
        assert result.state == startup.InitState.COMPLETED

        # Test skip result
        result = startup.initialize_bpod_system(
            choices=ConfigurableChoiceAdapter(),
            default_bpod_path=temp_setup.bpod_path,
            logger=get_logger(),
        )
        assert result.state == startup.InitState.SKIPPED
        assert result.message == "Bpod is already initialized and valid."


def test_create_system_config_dir_if_not_exists(
    temp_setup: TempSetup, monkeypatch: pytest.MonkeyPatch
):

    # temp_setup creates a valid system, should identify that
    assert startup._create_system_config_dir_if_not_exists(get_logger())

    # System config directory is created if it doesn't exist
    temp_setup.system_path.rmdir()
    assert startup._create_system_config_dir_if_not_exists(get_logger())
    assert temp_setup.system_path.exists()

    # Invalid path returns False
    if temp_setup.system_path.exists():
        temp_setup.system_path.rmdir()
    inaccessible_path = Path("/root/invalid_path_for_testing")
    monkeypatch.setattr(startup, "SYSTEM_CONFIG_DIR", inaccessible_path)
    monkeypatch.setattr(
        startup, "SYSTEM_CONFIG_FILE", inaccessible_path.joinpath("config.json")
    )
    assert not startup._create_system_config_dir_if_not_exists(get_logger())


def test_create_default_directories_with_invalid_path(temp_setup: TempSetup):
    # Provide an invalid path to create_default_directories
    invalid_path = Path("/root/invalid_path_for_testing")
    with pytest.raises(PermissionError):
        startup.create_default_directories(invalid_path)

    bpod_directory_path = temp_setup.bpod_path
    # Provide a valid path to create_default_directories
    startup.create_default_directories(bpod_directory_path)
    assert bpod_directory_path.exists()
    assert bpod_directory_path.joinpath("Config").exists()
    assert bpod_directory_path.joinpath("Logs").exists()
    assert bpod_directory_path.joinpath("Protocols").exists()
    assert bpod_directory_path.joinpath("Data").exists()


class TestCheckSystemIsInitialized:
    def test_happy_system_config_load(self, temp_setup: TempSetup):
        temp_setup.system_path.mkdir(parents=True, exist_ok=True)
        valid_config_path = temp_setup.system_path.joinpath("config.json")
        system_config = system_settings.SystemSettings.create(
            system_settings.BpodDir.create(temp_setup.bpod_path)
        )
        valid_config_path.write_text(system_config.model_dump_json())

        assert startup.check_system_is_initialized()

    def test_nonexistent_system_config_load(self, temp_setup: TempSetup):
        assert not startup.check_system_is_initialized(), "Folder shouldn't exist"
        temp_setup.system_path.mkdir(parents=True, exist_ok=True)
        assert not startup.check_system_is_initialized(), "File shouldn't exist"

    def test_malformed_system_config_load(self, temp_setup: TempSetup):
        # Create a malformed system config file
        temp_setup.system_path.mkdir(parents=True, exist_ok=True)
        malformed_config_path = temp_setup.system_path.joinpath("config.json")
        malformed_config_path.write_text(
            '{"key": "value",}'
        )  # Invalid JSON due to trailing comma

        assert not startup.check_system_is_initialized()

    def test_invalid_system_config_load(self, temp_setup: TempSetup):
        # Create a system config file with missing required fields
        temp_setup.system_path.mkdir(parents=True, exist_ok=True)
        invalid_config_path = temp_setup.system_path.joinpath("config.json")
        invalid_config_path.write_text("{}")  # Empty JSON, missing required fields
        assert not startup.check_system_is_initialized()
