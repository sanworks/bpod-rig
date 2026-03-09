import shutil
import tempfile
from pathlib import Path

import pytest
from pydantic_core import ValidationError

from bpod_rig.config.system_settings import SystemSettings, BpodDir, load_system_configuration

JSON_STRING = '{"first_key":{"second_key": "1234"}}'


@pytest.fixture
def temp_config():
    """
    A pytest fixture that sets up a temporary directory structure and
    configuration objects for testing. It handles cleanup automatically
    after the test using it has finished.
    """
    # --- Setup ---
    bpod_dir = Path(tempfile.mkdtemp())
    config_dir = bpod_dir.joinpath("Config")
    sp = BpodDir(base_dir=bpod_dir)
    ss = SystemSettings(paths=sp)
    full_file_path = ss.paths.base_config_dir.joinpath("config.json")

    # Yield the created objects to the test function
    yield ss, config_dir, full_file_path, bpod_dir

    # --- Teardown ---
    shutil.rmtree(bpod_dir, ignore_errors=True)


class TestSave:
    def test_save(self, temp_config):
        """Tests that the configuration is saved to the default path correctly."""
        ss, config_dir, full_file_path, _ = temp_config
        config_dir.mkdir(exist_ok=True)
        save_path = ss.save_system_configuration()

        assert save_path == full_file_path
        assert full_file_path.exists()

        with open(full_file_path, "r") as fs:
            assert fs.read() == ss.model_dump_json(indent=2)

    def test_save_path_override(self, temp_config):
        """Tests that the configuration can be saved to a non-default directory."""
        ss, config_dir, _, bpod_dir = temp_config
        config_dir.mkdir(exist_ok=True)
        save_path = ss.save_system_configuration(
            save_dir_override=ss.paths.base_dir
        )

        alt_file_path = bpod_dir.joinpath("config.json")

        assert save_path == alt_file_path
        assert alt_file_path.exists()

        with open(alt_file_path, "r") as fs:
            assert fs.read() == ss.model_dump_json(indent=2)

    def test_invalid_default_path(self, temp_config):
        """Tests that saving errors if the default directory does not exist."""
        ss, _, _, _ = temp_config
        # Note: We don't create the config_dir here
        with pytest.raises(FileNotFoundError):
            _ = ss.save_system_configuration()

    def test_invalid_override_path(self, temp_config):
        """Tests that saving errors if the override directory does not exist."""
        ss, _, _, bpod_dir = temp_config
        invalid_dir = bpod_dir.joinpath("InvalidDir")
        with pytest.raises(FileNotFoundError):
            _ = ss.save_system_configuration(save_dir_override=invalid_dir)


class TestLoad:
    def test_load(self, temp_config):
        """Tests that a valid configuration file can be loaded into a SystemSettings object."""
        ss, config_dir, full_file_path, _ = temp_config
        config_dir.mkdir(exist_ok=True)

        with open(full_file_path, "w") as fs:
            fs.write(ss.model_dump_json(indent=2))

        loaded_system_settings = load_system_configuration(full_file_path)
        assert loaded_system_settings == ss

    def test_bad_json(self, temp_config):
        """Tests that loading errors when the file contains invalid JSON."""
        ss, config_dir, full_file_path, _ = temp_config
        config_dir.mkdir(exist_ok=True)

        with open(full_file_path, "w") as fs:
            fs.write(ss.model_dump_json(indent=2)[:-1])  # Write incomplete JSON

        with pytest.raises(ValueError):
            _ = load_system_configuration(full_file_path)

    def test_invalid_schema(self, temp_config):
        """Tests that loading returns None when the JSON does not match the pydantic model schema."""
        _, config_dir, full_file_path, _ = temp_config
        config_dir.mkdir(exist_ok=True)

        with open(full_file_path, "w") as fs:
            fs.write(JSON_STRING)
        with pytest.raises(ValidationError):
            _ = load_system_configuration(full_file_path)
