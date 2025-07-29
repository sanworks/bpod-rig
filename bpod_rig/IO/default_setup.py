"""Module to create the default Bpod directory and associated subdirs"""

import logging

from pathlib import Path

DEFAULT_SUBDIRS = ["Calibrations", "Data", "Protocols", "Settings"]
DEFAULT_DIR_NAME = "Bpod"

logger = logging.getLogger(__name__)


def create_default_directories(default_path_override: Path = None) -> Path:
    """
    Function creates the default Bpod folder structure in the users home directory
    or in a user-supplied path
    :param default_path_override: (pathlib.Path) Optional: path to override the default
    Bpod folder
    structure location
    :return: (pathlib.Path) Bpod directory path
    """

    default_root_location = Path.home()

    if default_path_override:
        default_root_location = default_path_override

    bpod_folder_path = default_root_location.joinpath(DEFAULT_DIR_NAME)

    if not bpod_folder_path.exists():
        logger.debug("Creating default Bpod directory in %s", default_root_location)
        bpod_folder_path.mkdir(parents=True, exist_ok=True)

    for _dir in DEFAULT_SUBDIRS:
        _path = bpod_folder_path.joinpath(_dir)
        if not _path.exists():
            logger.debug(
                "Creating default subdirectory [%s] in %s", _dir, bpod_folder_path
            )
            _path.mkdir(parents=True, exist_ok=True)

    return bpod_folder_path
