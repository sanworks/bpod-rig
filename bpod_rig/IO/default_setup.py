"""Module to create the default Bpod user directory and associated subdirs"""

import logging
import shutil
from pathlib import Path

from bpod_rig.examples import calibration, settings

DEFAULT_SUBDIRS = ["Config", "Calibration", "Protocols", "Data", "Logs"]
DEFAULT_DIR_NAME = "Bpod"

logger = logging.getLogger(__name__)


def create_default_directories(default_path_override: Path = None) -> Path:
    """
    Create the default Bpod folder structure for a given machine.

    By default, the Bpod directory will be created inside the user's Documents
    folder with the following top-level subdirectories:

        Bpod/
            Config/
            Calibration/
            Protocols/
            Data/

    This function only creates the directory structure — it does NOT populate
    default calibration or settings files. To copy default files, call
    `copy_default_files()` separately.

    Parameters
    ----------
    default_path_override : pathlib.Path, optional
        A path to override the default Bpod folder location. If not provided,
        the default location is `~/Documents/Bpod`.

    Returns
    -------
    pathlib.Path
        The path to the created Bpod directory.
    """

    # Default root is the Documents folder
    default_root_location = Path.home() / "Documents"

    if default_path_override:
        default_root_location = default_path_override

    bpod_folder_path = default_root_location / DEFAULT_DIR_NAME

    is_new_install = False

    if not bpod_folder_path.exists():
        logger.debug("Creating default Bpod user directory in %s", default_root_location)
        bpod_folder_path.mkdir(parents=True, exist_ok=True)
        is_new_install = True
    else: logger.debug("Bpod user directory found: %s", bpod_folder_path)



    # Create top-level subdirectories
    for subdir in DEFAULT_SUBDIRS:
        new_path = bpod_folder_path.joinpath(subdir)
        if not new_path.exists():
            logger.debug(
                "Creating default subdirectory [%s] in %s", subdir, bpod_folder_path
            )
            new_path.mkdir(parents=True, exist_ok=True)


    if is_new_install:
        logger.info("Bpod user directory initialized to %s", bpod_folder_path)


    return bpod_folder_path


def copy_default_files(bpod_folder_path: Path, override: bool = False):
    """
    Function to copy default settings and calibration .json files from the included
    examples package into the calibration and config folders.

    Parameters
    ----------
    bpod_folder_path : pathlib.Path
        Path to the Bpod directory
    override : bool, optional
        Overwrite any existing files

    Returns
    -------
    None
    """

    # Locate target Calibration and Settings directories for this machine
    calibration_dir = bpod_folder_path.joinpath("Calibration")
    settings_dir = bpod_folder_path.joinpath("Config")

    calibration_example_dir = Path(calibration.__path__[0])
    settings_example_dir = Path(settings.__path__[0])
    default_calibration_files = calibration_example_dir.glob("*.json")
    default_settings_files = settings_example_dir.glob("*.json")

    calibration_dir_contents = list(calibration_dir.iterdir())
    settings_dir_contents = list(settings_dir.iterdir())

    if len(calibration_dir_contents) == 0 or override:
        for cal_file in default_calibration_files:
            try:
                logger.debug("Copying %s to %s...", cal_file, calibration_dir)
                shutil.copy2(cal_file, calibration_dir)
            except Exception as e:  # NOQA PERF203
                logger.error("Error copying %s!", cal_file)
                raise e

    if len(settings_dir_contents) == 0 or override:
        for setting_file in default_settings_files:
            try:
                logger.debug("Copying %s to %s...", setting_file, settings_dir)
                shutil.copy2(setting_file, settings_dir)
            except Exception as e:  # NOQA PERF203
                logger.error("Error copying %s!", setting_file)
                raise e
