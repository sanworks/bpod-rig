"""Module implementing the Pydantic models for any system settings."""

import datetime
import logging
from pathlib import Path
from typing import Annotated, Optional

from pydantic import UUID4, Field, PastDate

from bpod_rig.config.base import ModelWithMetadata
from bpod_rig.config.bpod_settings import BpodPaths
from bpod_rig.defaults import (
    DEFAULT_PROTOCOL_DIR_NAME, DEFAULT_DATA_DIR_NAME,
    DEFAULT_CONFIG_DIR_NAME
)

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


class SystemPaths(ModelWithMetadata):
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
        Optional[Path],
        Field(
            title="Bpod Protocol Directory",
            description="Local directory where Bpod protocols are stored."
            " The Protocol explorer will list all valid protocols found"
            " in this directory.",
            default_factory=lambda data: system_path_factory(
                data, DEFAULT_PROTOCOL_DIR_NAME
            ),
        ),
    ] = None

    data_dir: Annotated[
        Optional[Path],
        Field(
            title="Bpod Data Directory",
            description="Local directory where data from protocol runs are stored.",
            default_factory=lambda data: system_path_factory(
                data, DEFAULT_DATA_DIR_NAME
            ),
        ),
    ] = None

    base_config_dir: Annotated[
        Optional[Path],
        Field(
            title="Bpod Configuration Directory",
            description="Local directory where Bpod configuration files are stored.",
            default_factory=lambda data: system_path_factory(
                data, DEFAULT_CONFIG_DIR_NAME
            ),
        ),
    ] = None

    log_dir: Annotated[
        Optional[Path],
        Field(
            title="Bpod Log Directory",
            description="Local directory where Bpod logs are stored.",
            # default_factory=lambda data: system_path_factory(
            #     data,
            #     DEFAULT_LOG_DIR_NAME
            # ),
            # TODO: Add log folder to initial configuration; until then this is optional
        ),
    ] = None


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
        SystemPaths,
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


    def update_modification_time(self) -> bool:
        """Update time the SystemSettings object was modified.

        Override update_modification_time to also update the modified_datetime metadata
        field of SystemSettings subfields

        Returns
        -------
        bool:
            True if all times were updated, False otherwise
        """
        all_success = True

        all_success &= super().update_modification_time()
        # Update the SystemSettings save time

        if self.bpod_dirs:
            for bpod_dir in self.bpod_dirs:
                all_success &= bpod_dir.update_modification_time()
        # Update the save time for each bpod_dir

        if self.paths:
            all_success &= self.paths.update_modification_time()
        # Update the save time for the system paths

        return all_success
