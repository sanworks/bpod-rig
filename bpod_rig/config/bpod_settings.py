"""Module implementing the Pydantic models for any Bpod-specific settings."""

from pathlib import Path
from typing import Annotated

from pydantic import Field

from bpod_rig.config.base import ModelWithMetadata, SettingsMetadata


class BpodPaths(ModelWithMetadata):
    """Path configuration for a unique Bpod instance.

    Use the `create()` class method to construct instances with automatic
    subdirectory path generation from the parent directory and bpod_id.
    """

    bpod_id: Annotated[
        str,
        Field(
            ...,
            title="Bpod ID",
            description="Unique identifier for each Bpod connected to the system;"
            " doubles as the name for the configuration sub directory name"
            " for this Bpod",
        ),
    ]

    parent_dir: Annotated[
        Path,
        Field(
            ...,
            title="Bpod directory parent directory",
            description="This is the parent directory to this unique Bpod's directory",
        ),
    ]

    unique_bpod_dir: Annotated[
        Path,
        Field(
            title="Directory for this unique Bpod",
            description="Absolute path to the directory for this unique Bpod",
        ),
    ]

    settings_dir: Annotated[
        Path,
        Field(
            title="Bpod Settings Subdirectory",
            description="Sub directory where Bpod settings files are "
            "stored for this unique Bpod",
        ),
    ]

    calibration_dir: Annotated[
        Path,
        Field(
            title="Bpod Calibration Directory",
            description="Local directory where Bpod calibration files are stored.",
        ),
    ]

    calibration_files: Annotated[
        dict[str, Path],
        Field(
            default_factory=dict,
            title="Bpod calibration files",
            description="Dictionary of calibration files found in the calibration "
            "directory for this Bpod.",
        ),
    ]

    @classmethod
    def create(
        cls,
        bpod_id: str,
        parent_dir: Path | str,
        *,
        unique_bpod_dir: Path | str | None = None,
        settings_dir: Path | str | None = None,
        calibration_dir: Path | str | None = None,
        calibration_files: dict[str, Path] | None = None,
        username: str | None = None,
        metadata: "SettingsMetadata | None" = None,
    ) -> "BpodPaths":
        """Factory method to create BpodPaths with automatic subdirectory paths.

        This is the recommended way to create BpodPaths instances. It automatically
        generates subdirectory paths based on the parent_dir and bpod_id if not
        explicitly provided.

        Parameters
        ----------
        bpod_id : str
            Unique identifier for this Bpod
        parent_dir : Path | str
            Parent directory for Bpod-specific folders
        unique_bpod_dir : Path | str | None, optional
            Override for unique Bpod directory (default: parent_dir/Machine-{bpod_id})
        settings_dir : Path | str | None, optional
            Override for settings directory (default: unique_bpod_dir/Settings)
        calibration_dir : Path | str | None, optional
            Override for calibration directory (default: unique_bpod_dir/Calibration)
        calibration_files : dict[str, Path] | None, optional
            Calibration files dictionary
        username : str | None, optional
            Username for metadata
        metadata : SettingsMetadata | None, optional
            Pre-constructed metadata object

        Returns
        -------
        BpodPaths
            Fully initialized BpodPaths instance with all subdirectory paths populated

        Examples
        --------
        >>> paths = BpodPaths.create(bpod_id="1234", parent_dir="/home/user/Bpods")
        >>> paths.unique_bpod_dir
        PosixPath('/home/user/Bpods/Machine-1234')
        """
        parent_dir = Path(parent_dir)
        unique_bpod_dir = Path(
            unique_bpod_dir or parent_dir.joinpath(f"Machine-{bpod_id}")
        )
        settings_dir = Path(settings_dir or unique_bpod_dir.joinpath("Settings"))
        calibration_dir = Path(
            calibration_dir or unique_bpod_dir.joinpath("Calibration")
        )
        calibration_files = (
            {} if calibration_files is None else dict(calibration_files)
        )  # shallow copy to ensure immutability
        metadata = metadata or SettingsMetadata(username=username or None)

        return cls(
            bpod_id=bpod_id,
            parent_dir=parent_dir,
            unique_bpod_dir=unique_bpod_dir,
            settings_dir=settings_dir,
            calibration_dir=calibration_dir,
            calibration_files=calibration_files,
            metadata=metadata,
        )
