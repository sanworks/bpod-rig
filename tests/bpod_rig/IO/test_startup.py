import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from bpod_rig.IO import startup


class TestCreateDefaultDirectories:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self) -> Generator[None, None, None]:
        """Setup and teardown."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.bpod_path = self.temp_path / "Bpod"

        yield  # test runs here

        self.temp_dir.cleanup()

    def test_folder_creation(self) -> None:
        startup.create_default_directories(self.bpod_path)
        assert self.bpod_path.exists()
