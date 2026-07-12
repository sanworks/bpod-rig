import datetime
from pathlib import Path
from typing import TypedDict

import pytest
from pydantic import ValidationError

from bpod_rig.config.base import SettingsMetadata
from bpod_rig.config.bpod_settings import BpodPaths
from bpod_rig.config.system_settings import BpodDir, SystemSettings


class TestMetadataModel:
    def test_default(self):  # NOQA N802
        """Tests the default values of the SettingsMetadata model."""
        bm = SettingsMetadata()
        assert bm.creation_date == datetime.date.today()
        assert bm.modified_datetime is None
        assert bm.username == "BpodUser"

    def test_good_manual_vals(self) -> None:
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

    def test_validator_failure(self) -> None:
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


class TestSystemPathsModel:
    @pytest.fixture
    def paths(self, tmp_path: Path) -> dict[str, Path]:
        """Fixture to provide a common set of path objects for tests."""
        working_dir = tmp_path
        bpod_dir = working_dir.joinpath("Bpod")
        return {
            "bpod_dir": bpod_dir,
            "config_dir": bpod_dir.joinpath("Config"),
            "protocol_dir": bpod_dir.joinpath("Protocols"),
            "data_dir": bpod_dir.joinpath("Data"),
        }

    def test_default_factory(self, paths: dict[str, Path]) -> None:
        """Tests that the default directory paths are constructed correctly."""
        sp = BpodDir.create(base_dir=paths["bpod_dir"])
        assert sp.data_dir == paths["data_dir"]
        assert sp.base_config_dir == paths["config_dir"]
        assert sp.protocol_dir == paths["protocol_dir"]

    def test_pass_username(self, paths: dict[str, Path]) -> None:
        """Tests that a username can be passed through to the metadata."""
        paths["bpod_dir"].mkdir(exist_ok=True)
        paths["data_dir"].mkdir(exist_ok=True)
        paths["protocol_dir"].mkdir(exist_ok=True)
        paths["config_dir"].mkdir(exist_ok=True)

        sp = BpodDir.create(base_dir=paths["bpod_dir"], username="valid_username")

        # Does username get forwarded properly to the SettingsMetadata object
        assert sp.metadata.username == "valid_username"

        # Does the SettingsMetadata object get properly forwarded
        md = SettingsMetadata()
        sp2 = BpodDir.create(
            base_dir=paths["bpod_dir"], metadata=md, username="beepbop"
        )
        assert sp2.metadata.username != "beepbop"

    def test_not_paths(self) -> None:
        """Tests that non-path inputs for directories raise validation errors."""
        with pytest.raises(TypeError):
            BpodDir.create(base_dir=1234321)  # type: ignore

        sp = BpodDir.create(base_dir="/this/is/a/path")
        assert isinstance(sp.base_dir, Path)


class BpodPathsDict(TypedDict):
    base_dir: Path
    bpod_id: str
    bpod_dir: Path
    config_dir: Path
    calibration_dir: Path


class TestBpodPathsModel:
    @pytest.fixture
    def paths(self, tmp_path: Path) -> BpodPathsDict:
        """Fixture to provide a common set of Bpod-specific path objects."""
        working_dir = tmp_path
        base_dir = working_dir.joinpath("Bpods")
        bpod_id = "1234"
        bpod_dir = base_dir.joinpath(f"Machine-{bpod_id}")
        return {
            "base_dir": base_dir,
            "bpod_id": bpod_id,
            "bpod_dir": bpod_dir,
            "config_dir": bpod_dir.joinpath("Settings"),
            "calibration_dir": bpod_dir.joinpath("Calibration"),
        }

    def test_id_validation(self, paths: BpodPathsDict) -> None:
        """Tests validation for the bpod_id field."""
        # No ID, fails validation
        with pytest.raises(TypeError):
            BpodPaths.create(parent_dir=paths["bpod_dir"])  # type: ignore

        # ID is wrong type
        with pytest.raises(ValidationError):
            BpodPaths.create(bpod_id=1234, parent_dir=paths["bpod_dir"])  # type: ignore

        # No parent_dir
        with pytest.raises(TypeError):
            BpodPaths.create(bpod_id=paths["bpod_id"])  # type: ignore

        bp = BpodPaths.create(bpod_id=paths["bpod_id"], parent_dir=paths["base_dir"])
        assert bp.bpod_id == paths["bpod_id"]

    def test_default_factory(self, paths: BpodPathsDict) -> None:
        """Tests that the Bpod-specific paths are constructed correctly."""
        bp = BpodPaths.create(bpod_id=paths["bpod_id"], parent_dir=paths["base_dir"])
        assert bp.unique_bpod_dir == paths["bpod_dir"]
        assert bp.parent_dir == paths["base_dir"]
        assert bp.calibration_dir == paths["calibration_dir"]
        assert bp.settings_dir == paths["config_dir"]


class TestSystemSettingsModel:
    @pytest.fixture
    def paths(self, tmp_path: Path) -> dict[str, BpodDir]:
        """Fixture to provide a common set of path objects for tests."""
        working_dir = tmp_path
        bpod_dir = working_dir.joinpath("Bpod")
        system_paths = BpodDir.create(base_dir=bpod_dir)
        return {"system_paths": system_paths}

    def test_default(self, paths: dict[str, BpodDir]) -> None:
        """Tests that the default system settings are constructed correctly."""
        settings = SystemSettings.create(paths=paths["system_paths"])

        assert settings.current_version == "0.0.0"
        assert settings.last_update_check is None
        assert settings.phone_home_id is None
        assert not settings.phone_home_opt_in
        assert not settings.debug
        assert settings.paths == paths["system_paths"]
        assert settings.bpod_dirs is None
