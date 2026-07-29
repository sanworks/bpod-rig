"""Module implementing the Pydantic models for any system settings."""

from pathlib import Path
from typing import Annotated

from pydantic import UUID4, Field, PastDate

from bpod_rig import log
from bpod_rig.config.base import ModelWithMetadata, SettingsMetadata
from bpod_rig.config.bpod_paths import BpodPaths_2
from bpod_rig.defaults import (
 SYSTEM_DIR,
)

logger = log.get_logger(__name__)


class SystemSettings(ModelWithMetadata):
    current_version: Annotated[
        str,
        Field(
            title="Current bpod-rig version",
            description="Currently installed version of the bpod-rig repository",
        ),
    ]

    last_update_check: Annotated[
        PastDate | None,
        Field(
            title="Last update check date and time",
            description="Last date and time that system checked for any updates"
            " compared to the current version",
        ),
    ] = None

    phone_home_id: Annotated[
        UUID4 | None,
        Field(
            title="System's Unique Phone-Home ID",
            description="UUID4 ID of the current system"
            " for the Bpod phone-home telemetry.",
        ),
    ] = None

    phone_home_opt_in: Annotated[
        bool,
        Field(
            title="Phone-Home Opt-In",
            description="Whether or not the user has opted"
            " in to the phone-home telemetry.",
        ),
    ]

    debug: Annotated[
        bool,
        Field(
            title="Debug Enabled",
            description="Set to True to enable debug information output.",
        ),
    ]

    paths: Annotated[
        BpodPaths_2,
        Field(
            title="System Paths Model",
            description="Model containing validated bpod system paths",
        ),
    ]

    @classmethod
    def create(
        cls,
        paths: BpodPaths_2,
        *,
        current_version: str = "0.0.0",
        phone_home_opt_in: bool = False,
        debug: bool = False,
        username: str | None = None,
        metadata: "SettingsMetadata | None" = None,
    ) -> "SystemSettings":
        """Factory method to create SystemSettings with automatic metadata handling.

        This is the recommended way to create SystemSettings instances.

        Parameters
        ----------
        paths : BpodPaths_2
            System paths configuration
        current_version : str, optional
            Currently installed version (default: "0.0.0")
        phone_home_opt_in : bool, optional
            Whether user opted into telemetry (default: False)
        debug : bool, optional
            Enable debug output (default: False)
        username : str | None, optional
            Username for metadata
        metadata : SettingsMetadata | None, optional
            Pre-constructed metadata object

        Returns
        -------
        SystemSettings
            Fully initialized SystemSettings instance

        Examples
        --------
        >>> bpod_paths = BpodPaths_2.create("/home/user/Bpod")
        >>> settings = SystemSettings.create(paths=bpod_paths, username="TestUser")
        >>> settings.metadata.username
        'TestUser'
        """
        return cls(
            paths=paths,
            current_version=current_version,
            phone_home_opt_in=phone_home_opt_in,
            debug=debug,
            metadata=metadata or SettingsMetadata(username=username),
        )

    def update_modification_time(self) -> None:
        """Update time the SystemSettings object was modified.

        Override update_modification_time to also update the modified_datetime metadata
        field of SystemSettings subfields

        Returns
        -------
        None
        """
        super().update_modification_time()
        # Update the SystemSettings save time

        if self.paths:
            self.paths.update_modification_time()
        # Update the save time for the system paths

    def save_system_configuration(self, save_dir_override: Path | None = None) -> Path:
        """
        Save SystemSettings instance to disk as json-formatted text.

        Simultaneously will update the save_time field

        Parameters
        ----------
        save_dir_override : Path, optional
            Optional Path to override the default save directory. If not provided,
            SYSTEM_DIR will be used.

        Returns
        -------
            Path
                Path to the saved file is returned
        """

        logger.info("Saving system configuration as JSON!")
        self.update_modification_time()

        save_dir = SYSTEM_DIR

        if save_dir_override is not None:
            save_dir = save_dir_override

        logger.debug("Save directory for SystemSettings set to %s: ", save_dir)
        self.save_model(save_dir, "config")
        return save_dir.joinpath("config.json")


def load_system_configuration(config_file_path: Path) -> SystemSettings:
    """
    Load JSON from disk and validate it against the SystemSettings schema.

    If valid JSON is read from disk, parsed, and validated, an initialized
    SystemSettings object is returned.

    Parameters
    ----------
    config_file_path : pathlib.Path
        Path to the JSON file to load and validate

    Returns
    -------
    SystemSettings
        An instance of the SystemSettings model created from
        the provided configuration file is returned


    """
    return SystemSettings.model_validate_json(config_file_path.read_text())
