import datetime
from pathlib import Path
from typing import TypedDict

import pytest
from pydantic import ValidationError

from bpod_rig.config.base import SettingsMetadata
from bpod_rig.config.bpod_paths import BpodPaths_2
from bpod_rig.config.system_settings import SystemSettings


class TestMetadataModel:
    def test_default(self):
        """Tests the default values of the SettingsMetadata model."""
        bm = SettingsMetadata()
        assert bm.creation_date == datetime.date.today()
        assert bm.modified_datetime is None
        assert bm.username == "BpodUser"

    def test_good_manual_vals(self):
        """Tests creating a SettingsMetadata model with valid manual values."""
        past_creation_date = datetime.date(2025, 1, 1)
        past_save_datetime = datetime.datetime(2025, 2, 1)
        new_user = "TestUser"

        bm = SettingsMetadata(
            creation_date=past_creation_date,
            modified_datetime=past_save_datetime,
            username=new_user,
        )

        assert bm.creation_date == past_creation_date
        assert bm.modified_datetime == past_save_datetime
        assert bm.username == new_user

    def test_validator_failure(self):
        """Tests that pydantic validators raise ValidationErrors for bad data."""
        with pytest.raises(ValidationError):
            future_creation_date = datetime.date(3000, 1, 1)
            SettingsMetadata(creation_date=future_creation_date)

        with pytest.raises(ValidationError):
            future_save_datetime = datetime.datetime.now() + datetime.timedelta(hours=1)
            SettingsMetadata(modified_datetime=future_save_datetime)

        with pytest.raises(ValidationError):
            too_long_username = "a" * 200
            SettingsMetadata(username=too_long_username)

        with pytest.raises(ValidationError):
            too_short_username = ""
            SettingsMetadata(username=too_short_username)


class BpodPathsDict(TypedDict):
    base_dir: Path
    protocol_dir: Path
    data_dir: Path
    log_dir: Path
    bpods_dir: Path
    calibration_dir: Path
    calibration_files: dict[str, Path]


class TestBpodPathsModel:
    @pytest.fixture
    def paths(self, tmp_path: Path) -> BpodPathsDict:
        """Fixture to provide a common set of Bpod-specific path objects."""
        working_dir = tmp_path
        base_dir = working_dir.joinpath("Bpod")
        return {
            "base_dir": base_dir,
            "protocol_dir": base_dir.joinpath("Protocols"),
            "data_dir": base_dir.joinpath("Data"),
            "log_dir": base_dir.joinpath("Logs"),
            "bpods_dir": base_dir.joinpath("Bpods"),
            "calibration_dir": base_dir.joinpath("Calibration"),
            "calibration_files": {},
        }

    def test_pass_username(self, paths: BpodPathsDict):
        sp = BpodPaths_2.create(base_dir=paths["base_dir"], username="valid_username")
        # Does username get forwarded properly to the SettingsMetadata object
        assert sp.metadata.username == "valid_username"

        # Does the SettingsMetadata object get properly forwarded
        md = SettingsMetadata()
        sp2 = BpodPaths_2.create(
            base_dir=paths["base_dir"], metadata=md, username="beepbop"
        )
        assert sp2.metadata.username != "beepbop"

    def test_validation(self, paths: BpodPathsDict):
        """Tests validation for the bpod_id field."""
        # No path, fails validation
        with pytest.raises(TypeError):
            BpodPaths_2.create()  # type: ignore

        # path is wrong type
        with pytest.raises(TypeError):
            BpodPaths_2.create(base_dir=1234)  # type: ignore

        bp = BpodPaths_2.create(base_dir=paths["base_dir"])
        assert bp.base_dir == paths["base_dir"]

    def test_default_factory(self, paths: BpodPathsDict):
        """Tests that the Bpod-specific paths are constructed correctly."""
        bp = BpodPaths_2.create(base_dir=paths["base_dir"])
        assert bp.base_dir == paths["base_dir"]
        assert bp.protocol_dir == paths["protocol_dir"]
        assert bp.data_dir == paths["data_dir"]
        assert bp.log_dir == paths["log_dir"]
        assert bp.bpods_dir == paths["bpods_dir"]
        assert bp.calibration_dir == paths["calibration_dir"]
        assert bp.calibration_files == {}


class TestSystemSettingsModel:
    @pytest.fixture
    def paths(self, tmp_path: Path) -> dict[str, BpodPaths_2]:
        """Fixture to provide a common set of path objects for tests."""
        working_dir = tmp_path
        bpod_dir = working_dir.joinpath("Bpod")
        system_paths = BpodPaths_2.create(base_dir=bpod_dir)
        return {"system_paths": system_paths}

    def test_not_paths(self):
        with pytest.raises(TypeError):
            SystemSettings.create(paths=12345)  # type: ignore

    def test_default(self, paths: dict[str, BpodPaths_2]):
        """Tests that the default system settings are constructed correctly."""
        settings = SystemSettings.create(paths=paths["system_paths"])

        assert settings.current_version == "0.0.0"
        assert settings.last_update_check is None
        assert settings.phone_home_id is None
        assert not settings.phone_home_opt_in
        assert not settings.debug
        assert settings.paths == paths["system_paths"]
