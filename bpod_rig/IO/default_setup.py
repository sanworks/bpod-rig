"""Module to create the default Bpod directory and associated subdirs"""

import logging
import shutil

from pathlib import Path

from examples import calibration, settings

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

def copy_default_files(bpod_dir: Path, only_if_empty:bool = True):
    """
    Function to copy default settings and calibration .json files from the included
    examples package
    :param bpod_dir: (pathlib.Path): Path to the Bpod directory
    :param only_if_empty: (bool) (Optional): Only copy the files if the destination
     directory is empty
    :return:
    """
    calibration_example_dir = Path(calibration.__path__[0])
    settings_example_dir = Path(settings.__path__[0])
    default_calibration_files = calibration_example_dir.glob("*.json")
    default_settings_files = settings_example_dir.glob("*.json")

    bpod_calibration_dir = bpod_dir.joinpath("Calibrations")
    bpod_settings_dir = bpod_dir.joinpath("Settings")
    bpod_calibration_dir_contents = list(bpod_calibration_dir.iterdir())
    bpod_settings_dir_contents = list(bpod_settings_dir.iterdir())


    if (
        (only_if_empty and len(bpod_calibration_dir_contents) == 0) or
        not only_if_empty
    ):
        # If only_if_empty is true, the calibration dir must be empty; if only_if_empty
        # is false, we'll copy no matter what
        for cal_file in default_calibration_files:
            try:
                logger.debug("Copying %s to %s...", cal_file, bpod_calibration_dir)
                shutil.copy2(cal_file, bpod_calibration_dir)
            except Exception as e:
                logger.error("Error copying %s! Original Exception: %s", cal_file, e)

    if (
        (only_if_empty and len(bpod_settings_dir_contents) == 0) or
        not only_if_empty
    ):
        for setting_file in default_settings_files:
            try:
                logger.debug("Copying %s to %s...", setting_file, bpod_settings_dir)
                shutil.copy2(setting_file, bpod_settings_dir)
            except Exception as e:
                logger.error("Error copying %s! Original Exception: %s", setting_file, e)

