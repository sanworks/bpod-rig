"""Module to create the default Bpod user directory and associated subdirs."""

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
        logger.debug(
            "Creating default Bpod user directory in %s", default_root_location
        )
        bpod_folder_path.mkdir(parents=True, exist_ok=True)
        is_new_install = True
    else:
        logger.debug("Bpod user directory found: %s", bpod_folder_path)

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


def create_default_path_file(user_defined_path: Path, file_save_location: Path = None):
    """
    Writes the user-defined default path into a file in the default Bpod folder so it
    can be retrieved later.

    By default, the Bpod directory is located in the user's 'Documents/Bpod/' directory.
    If the user chooses to override that directory, a persistent link to that directory
    is written to a .txt file in the default directory to reference later.

    Parameters
    ----------
    user_defined_path : pathlib.Path
        User-defined default Bpod Path
    file_save_location : pathlib.Path, optional
        Path to save the bpod_path.txt pointer file to. If not provided defaults to
        [USER_HOME_DIR]/Documents/Bpod/

        Used for testing purposes. Should not be used in normal operation.

    Raises:
        FileNotFoundError
            If the file_save_location parameter does not exist, this error is raised

    """

    if not file_save_location:
        file_save_location = Path.home() / "Documents/Bpod/"
    else:
        if not file_save_location.exists():
            logger.error(
                "File save directory %s does not exist!",
                file_save_location
            )
            raise FileNotFoundError(
                "File save directory %s does not exist!",
                file_save_location
            )

    pointer_file_path = file_save_location / "bpod_path.txt"

    try:
        pointer_file_path.write_text(str(user_defined_path))
    except Exception as e:
        logger.error("Error writing default path pointer file: %s")
        raise e

def get_default_path_file() -> Path:
    """
    Returns the path to the default Bpod directory if the user chose to store it in a
    directory other than the default 'Documents/Bpod' directory.

    Returns
    -------
    Pathlib.Path:
        Path to the user-defined default Bpod directory

    """
    pointer_file_path = Path.home() / "Documents/Bpod/bpod_path.txt"

    try:
        if pointer_file_path.exists():
            default_path_pointer = pointer_file_path.read_text()
            return Path(default_path_pointer)

        raise FileNotFoundError(
            "Default path pointer file %s not found!", pointer_file_path
        )
    except Exception as e:
        logger.error("Error reading default path pointer file: %s", pointer_file_path)
        raise e
