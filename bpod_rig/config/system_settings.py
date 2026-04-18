"""Module implementing the Pydantic models for any system settings."""

import logging
from pathlib import Path
from typing import Annotated, Optional

from pydantic import UUID4, Field, PastDate
from pydantic_core import from_json

from bpod_rig.config.base import ModelWithMetadata, SettingsMetadata
from bpod_rig.config.bpod_settings import BpodPaths
from bpod_rig.defaults import (
    DEFAULT_CONFIG_DIR_NAME,
    DEFAULT_DATA_DIR_NAME,
    DEFAULT_PROTOCOL_DIR_NAME,
    SYSTEM_CONFIG_DIR,
)
from bpod_rig.IO import json_handler

logger = logging.getLogger(__name__)


def system_path_factory(data: dict, addition: str) -> Path | None:
    """
    Function to dynamically create SystemPath subpaths at validation time.

    Function creates a path in the below form:
        {base_dir}/[addition]
    Path components in {} are retrieved from the dictionary of pre-validated data.

    Parameters
    ----------
    data : dict
        Dictionary containing all previously validated fields
    addition : str
        Addition to join to the end of the path.

    Returns
    -------
    pathlib.Path
        Combined path in above form.
    """
    if "base_dir" not in data:
        return None

    return data["base_dir"].joinpath(addition)


class BpodDir(ModelWithMetadata):
    """Bpod directory structure with required subdirectories.

    Use the `create()` class method to construct instances with automatic
    subdirectory path generation from the base directory.
    """

    base_dir: Annotated[
        Path,
        Field(
            ...,
            title="Local Bpod Directory",
            description="Local Bpod base directory where other folders are stored."
            " There is not any data directly stored in this directory",
            examples=[
                r"C:\Users\BpodUser\Documents\Bpod",
                "/home/BpodUser/Documents/Bpod",
            ],
        ),
    ]

    protocol_dir: Annotated[
        Path,
        Field(
            title="Bpod Protocol Directory",
            description="Local directory where Bpod protocols are stored."
            " The Protocol explorer will list all valid protocols found"
            " in this directory.",
        ),
    ]

    data_dir: Annotated[
        Path,
        Field(
            title="Bpod Data Directory",
            description="Local directory where data from protocol runs are stored.",
        ),
    ]

    base_config_dir: Annotated[
        Path,
        Field(
            title="Bpod Configuration Directory",
            description="Local directory where Bpod configuration files are stored.",
        ),
    ]

    log_dir: Annotated[
        Optional[Path],
        Field(
            title="Bpod Log Directory",
            description="Local directory where Bpod logs are stored.",
            # TODO: Add log folder to initial configuration; until then this is optional
        ),
    ] = None

    @classmethod
    def create(
        cls,
        base_dir: Path | str,
        *,
        protocol_dir: Path | str | None = None,
        data_dir: Path | str | None = None,
        base_config_dir: Path | str | None = None,
        log_dir: Path | str | None = None,
        username: str | None = None,
        metadata: "SettingsMetadata | None" = None,
    ) -> "BpodDir":
        """Factory method to create BpodDir with automatic subdirectory paths.

        This is the recommended way to create BpodDir instances. It automatically
        generates subdirectory paths based on the base_dir if not explicitly provided.

        Parameters
        ----------
        base_dir : Path | str
            Base Bpod directory
        protocol_dir : Path | str | None, optional
            Override for protocol directory (default: base_dir/Protocols)
        data_dir : Path | str | None, optional
            Override for data directory (default: base_dir/Data)
        base_config_dir : Path | str | None, optional
            Override for config directory (default: base_dir/Config)
        log_dir : Path | str | None, optional
            Optional log directory
        username : str | None, optional
            Username for metadata
        metadata : SettingsMetadata | None, optional
            Pre-constructed metadata object

        Returns
        -------
        BpodDir
            Fully initialized BpodDir instance with all subdirectory paths populated

        Examples
        --------
        >>> bpod_dir = BpodDir.create(base_dir="/home/user/Bpod")
        >>> bpod_dir.protocol_dir
        PosixPath('/home/user/Bpod/Protocols')
        """
        base_dir = Path(base_dir)
        protocol_dir = Path(protocol_dir or base_dir / DEFAULT_PROTOCOL_DIR_NAME)
        data_dir = Path(data_dir or base_dir / DEFAULT_DATA_DIR_NAME)
        base_config_dir = Path(base_config_dir or base_dir / DEFAULT_CONFIG_DIR_NAME)
        log_dir = Path(log_dir) if log_dir else None

        return cls(
            base_dir=base_dir,
            protocol_dir=protocol_dir,
            data_dir=data_dir,
            base_config_dir=base_config_dir,
            log_dir=log_dir,
            metadata=metadata or SettingsMetadata(username=username or None),
        )

    def verify(self) -> bool:
        dir_verified = True
        sp_fields = BpodDir.model_fields
        sp_fields = [field for field in sp_fields if field != "metadata"]
        sp_as_dict = self.model_dump()

        for field in sp_fields:
            field_path = sp_as_dict[field]
            if field_path is None:
                continue
                # Skip None values that are not implemented yet
            if not field_path.exists():
                logger.error("Bpod subdirectory %s does not exist", field_path)
                dir_verified = False

        return dir_verified

    def save_system_paths(self, save_dir_override: Path | None) -> None:
        """
        Save the system paths to the system configuration directory as
        json-formatted text.

        Simultaneously will update the save_time field

        Parameters
        ----------
        save_dir_override : Path | None
            Optional Path to override the default save directory.
            Default SYSTEM_CONFIG_DIR used if not provided

        Returns
        -------
        None
        """
        logger.debug("Saving system paths as JSON!")
        self.update_modification_time()

        if save_dir_override is not None:
            save_dir = save_dir_override
        else:
            save_dir = SYSTEM_CONFIG_DIR

        system_paths_json = self.model_dump_json(indent=2)
        json_handler.write_json(system_paths_json, save_dir, "paths")


class SystemSettings(ModelWithMetadata):
    current_version: Annotated[
        str,
        Field(
            title="Current bpod-rig version",
            description="Currently installed version of the bpod-rig repository",
        ),
    ] = "0.0.0"

    last_update_check: Annotated[
        Optional[PastDate],
        Field(
            title="Last update check date and time",
            description="Last date and time that system checked for any updates"
            " compared to the current version",
        ),
    ] = None

    phone_home_id: Annotated[
        Optional[UUID4],
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
    ] = False

    debug: Annotated[
        bool,
        Field(
            False,
            title="Debug Enabled",
            description="Set to True to enable debug information output.",
        ),
    ] = False

    paths: Annotated[
        BpodDir,
        Field(
            title="System Paths Model",
            description="Model containing validated bpod system paths",
        ),
    ]

    bpod_dirs: Annotated[
        Optional[list[BpodPaths]],
        Field(
            title="All Bpod Paths",
            description="List containing BpodPaths objects that contain"
            " the folder structure for each unique Bpod",
        ),
    ] = None

    def update_modification_time(self):
        """Update time the SystemSettings object was modified.

        Override update_modification_time to also update the modified_datetime metadata
        field of SystemSettings subfields

        Returns
        -------
        None
        """
        super().update_modification_time()
        # Update the SystemSettings save time

        if self.bpod_dirs:
            for bpod_dir in self.bpod_dirs:
                bpod_dir.update_modification_time()
        # Update the save time for each bpod_dir

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
            system_settings.paths.base_config_dir will be used.

        Returns
        -------
            Path
                Path to the saved file is returned
        """
        logger.info("Saving system configuration as JSON!")
        self.update_modification_time()

        if save_dir_override is None:
            save_dir = self.paths.base_config_dir
        else:
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
    logger.debug("Attempting to read, parse, and validate: %s", config_file_path)

    file_content_json = json_handler.read_json(config_file_path)
    json_object = from_json(file_content_json, allow_partial=False)
    return SystemSettings.model_validate(json_object)
