import pathlib
import shutil
import tempfile

import pytest

from bpod_rig.examples import copy, calibration, settings

@pytest.fixture()
def temp_dirs():
    temp_dest_dir = pathlib.Path(tempfile.mkdtemp())

    yield temp_dest_dir

    shutil.rmtree(temp_dest_dir, ignore_errors=True)

class TestCopyExamples:
    def test_copy(self, temp_dirs):
        calibration_dir = temp_dirs.joinpath("calibration")
        settings_dir = temp_dirs.joinpath("settings")
        calibration_dir.mkdir()
        settings_dir.mkdir()


        copy.copy_examples('calibration', calibration_dir)
        copy.copy_examples('settings', settings_dir)

        # This will not be robust if we also start copying directories,
        # but for just files it will work for now
        expected_cal_files = get_names_in_path(calibration.__path__[0])
        expected_settings_files = get_names_in_path(settings.__path__[0])

        cal_contents = get_names_in_path(calibration_dir)
        settings_contents = get_names_in_path(settings_dir)

        for file in expected_cal_files:
            assert file in cal_contents

        for file in expected_settings_files:
            assert file in settings_contents

    def test_invalid_key(self):
        with pytest.raises(ValueError):
            copy.copy_examples('invalid_key', pathlib.Path())

    def test_invalid_path(self, temp_dirs):
        with pytest.raises(FileNotFoundError):
            copy.copy_examples('calibration', temp_dirs.joinpath("~~(__^·>"))
            # The directory ~~(__^·> (mouse) does not exist!

            
def get_names_in_path(path: pathlib.Path | str) -> list[str]:
    if isinstance(path, str):
        path = pathlib.Path(path)

    return [item.name for item in path.iterdir()]
