import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import TypedDict

import pytest
from pydantic_core import ValidationError

from bpod_rig.config.system_settings import (
    BpodDir,
    SystemSettings,
    load_system_configuration,
)

JSON_STRING = '{"first_key":{"second_key": "1234"}}'


class TempConfigDict(TypedDict):
    system_settings: SystemSettings
    config_dir: Path
    full_file_path: Path
    bpod_dir: Path


@pytest.fixture
def temp_config() -> Generator[TempConfigDict, None, None]:
    """
    A pytest fixture that sets up a temporary directory structure and
    configuration objects for testing. It handles cleanup automatically
    after the test using it has finished.
    """
    # --- Setup ---
    bpod_dir = Path(tempfile.mkdtemp())
    config_dir = bpod_dir.joinpath("Config")
    sp = BpodDir.create(base_dir=bpod_dir)
    ss = SystemSettings.create(paths=sp)
    full_file_path = ss.paths.base_config_dir.joinpath("config.json")

    # Yield the created objects to the test function
    yield TempConfigDict(
        system_settings=ss,
        config_dir=config_dir,
        full_file_path=full_file_path,
        bpod_dir=bpod_dir,
    )

    # --- Teardown ---
    shutil.rmtree(bpod_dir, ignore_errors=True)


class TestSave:
    def test_save(self, temp_config: TempConfigDict) -> None:
        """Tests that the configuration is saved to the default path correctly."""
        temp_config["config_dir"].mkdir(exist_ok=True)
        save_path = temp_config["system_settings"].save_system_configuration()
        full_file_path = temp_config["full_file_path"]

        assert save_path == full_file_path
        assert full_file_path.exists()

        with full_file_path.open() as fs:
            assert fs.read() == temp_config["system_settings"].model_dump_json(indent=2)

    def test_save_path_override(self, temp_config: TempConfigDict) -> None:
        """Tests that the configuration can be saved to a non-default directory."""
        temp_config["config_dir"].mkdir(exist_ok=True)
        save_path = temp_config["system_settings"].save_system_configuration(
            save_dir_override=temp_config["system_settings"].paths.base_dir
        )

        alt_file_path = temp_config["bpod_dir"].joinpath("config.json")

        assert save_path == alt_file_path
        assert alt_file_path.exists()

        with alt_file_path.open() as fs:
            assert fs.read() == temp_config["system_settings"].model_dump_json(indent=2)

    def test_invalid_default_path(self, temp_config: TempConfigDict) -> None:
        """Tests that saving errors if the default directory does not exist."""
        # Note: We don't create the config_dir here
        with pytest.raises(FileNotFoundError):
            _ = temp_config["system_settings"].save_system_configuration()

    def test_invalid_override_path(self, temp_config: TempConfigDict) -> None:
        """Tests that saving errors if the override directory does not exist."""
        invalid_dir = temp_config["bpod_dir"].joinpath("InvalidDir")
        with pytest.raises(FileNotFoundError):
            _ = temp_config["system_settings"].save_system_configuration(
                save_dir_override=invalid_dir
            )


class TestLoad:
    def test_load(self, temp_config: TempConfigDict) -> None:
        """Tests that a valid configuration file can be loaded
        into a SystemSettings object.
        """
        temp_config["config_dir"].mkdir(exist_ok=True)

        with temp_config["full_file_path"].open("w") as fs:
            fs.write(temp_config["system_settings"].model_dump_json(indent=2))

        loaded_system_settings = load_system_configuration(
            temp_config["full_file_path"]
        )
        assert loaded_system_settings == temp_config["system_settings"]

    def test_bad_json(self, temp_config: TempConfigDict) -> None:
        """Tests that loading errors when the file contains invalid JSON."""
        temp_config["config_dir"].mkdir(exist_ok=True)

        with temp_config["full_file_path"].open("w") as fs:
            fs.write(
                temp_config["system_settings"].model_dump_json(indent=2)[:-1]
            )  # Write incomplete JSON

        with pytest.raises(ValueError):
            _ = load_system_configuration(temp_config["full_file_path"])

    def test_invalid_schema(self, temp_config: TempConfigDict) -> None:
        """
        Tests that loading returns None when the JSON does not match the pydantic
        model schema.
        """
        temp_config["config_dir"].mkdir(exist_ok=True)

        with temp_config["full_file_path"].open("w") as fs:
            fs.write(JSON_STRING)
        with pytest.raises(ValidationError):
            _ = load_system_configuration(temp_config["full_file_path"])
