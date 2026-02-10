from pathlib import Path
import tempfile

import pytest


from bpod_rig.IO import startup


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
