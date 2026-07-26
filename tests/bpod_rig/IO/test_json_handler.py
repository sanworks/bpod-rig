import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from bpod_rig.IO import json_handler

JSON_STRING = '{"first_key":{"second_key": "1234"}}'


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    A pytest fixture that creates a temporary directory for a test
    and handles cleanup automatically after the test has finished.
    """
    # --- Setup ---
    tempdir_path = Path(tempfile.mkdtemp())
    yield tempdir_path
    # --- Teardown ---
    shutil.rmtree(tempdir_path, ignore_errors=True)


class TestJSONHandler:
    def test_save(self, temp_dir: Path) -> None:
        """Tests that a JSON string can be successfully written to a file."""
        full_path = temp_dir.joinpath("temp.json")

        returned_path = json_handler.write_json(JSON_STRING, temp_dir, "temp")

        assert returned_path == full_path
        assert full_path.exists()

        with full_path.open() as fs:
            file_content = fs.read()

        assert file_content == JSON_STRING

    def test_save_bad_path(self, temp_dir: Path) -> None:
        """Tests that write_json errors if the target directory does not exist."""
        bad_dir = temp_dir.joinpath("bad_dir")

        with pytest.raises(FileNotFoundError):
            _ = json_handler.write_json(JSON_STRING, bad_dir, "temp")

    def test_load(self, temp_dir: Path) -> None:
        """Tests that a JSON file can be successfully read."""
        test_file = temp_dir.joinpath("config.json")
        with test_file.open("w") as tf:
            tf.write(JSON_STRING)

        returned_data = json_handler.read_json(test_file)
        assert returned_data == JSON_STRING

    def test_load_bad_path(self, temp_dir: Path) -> None:
        """Tests that read_json returns None if the file does not exist."""
        bad_file = temp_dir.joinpath("dne.json")

        with pytest.raises(FileNotFoundError):
            _ = json_handler.read_json(bad_file)
