"""Module to create the default Bpod user directory and associated subdirs."""

import logging
import shutil
from pathlib import Path

from bpod_rig.examples import calibration, settings

DEFAULT_SUBDIRS = ["Config", "Calibration", "Protocols", "Data", "Logs"]
DEFAULT_DIR_NAME = "Bpod"

SYSTEM_CONFIG_DIR = platformdirs.user_config_path(DEFAULT_DIR_NAME)
DEFAULT_BPOD_PATH = platformdirs.user_documents_path() / DEFAULT_DIR_NAME

logger = logging.getLogger(__name__)

def create_default_directories(bpod_directory_path: Path = None) -> Path:
    """Create the default Bpod folder structure.

    The Bpod directory will be created inside the given path with the following
    top-level subdirectories:

        Bpod/
            Config/
            Calibration/
            Protocols/
            Data/
            Logs/

    This function only creates the directory structure — it does NOT populate
    default calibration or settings files. To copy default files, call
    `copy_default_files()` separately.

    Parameters
    ----------
    bpod_directory_path : pathlib.Path
        The path to initialize the Bpod folder location

    Returns
    -------
    pathlib.Path
        The path to the created Bpod directory.
    """
    is_new_install = False

    if not bpod_directory_path.exists():
        logger.debug(
            "Creating default Bpod user directory in %s", bpod_directory_path
        )
        bpod_directory_path.mkdir(parents=True, exist_ok=True)
        is_new_install = True
    else:
        logger.debug("Bpod user directory found: %s", bpod_directory_path)

    # Create top-level subdirectories
    for subdir in DEFAULT_SUBDIRS:
        new_path = bpod_directory_path.joinpath(subdir)
        if not new_path.exists():
            logger.debug(
                "Creating default subdirectory [%s] in %s", subdir, bpod_directory_path
            )
            new_path.mkdir(parents=True, exist_ok=True)

    if is_new_install:
        logger.info("Bpod user directory initialized to %s", bpod_directory_path)

    return bpod_directory_path


def copy_default_files(bpod_folder_path: Path, override: bool = False):
    """Function to copy default files into their respective folders.

    Copies the default calibration and configuration files from the examples module
    to their respective directories.

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
    """Writes the user-defined default path into a file.

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

    """
    if not file_save_location:
        file_save_location = Path.home() / "Documents/Bpod/"
    else:
        if not file_save_location.exists():
            logger.error("File save directory %s does not exist!", file_save_location)
            raise FileNotFoundError(
                "File save directory %s does not exist!", file_save_location
            )

    pointer_file_path = file_save_location / "bpod_path.txt"

    try:
        pointer_file_path.write_text(str(user_defined_path))
    except Exception as e:
        logger.error("Error writing default path pointer file: %s")
        raise e


def get_default_path_file() -> Path | None:
    """Returns the path to the default Bpod directory from the default directory.

    If the user chose to save the Bpod directory in a directory other than the default
    'Documents/Bpod', the user-defined path is saved to 'Documents/Bpod/bpod_path.txt'.
    This function reads and returns the user-defined path to the Bpod directory.

    Returns
    -------
    Pathlib.Path:
        Path to the user-defined default Bpod directory

    or

    None
        If bpod_path.txt does not exist, return None

    """
    pointer_file_path = Path.home() / "Documents/Bpod/bpod_path.txt"

    try:
        if pointer_file_path.exists():
            default_path_pointer = pointer_file_path.read_text()
            return Path(default_path_pointer)
        return None
        # If the file does not exist, return None

    except Exception as e:
        logger.error("Error reading default path pointer file: %s", pointer_file_path)
        raise e


def get_bpod_directory_path() -> Path:
    """Returns the path to the Bpod directory.

    Returns
    -------
    Pathlib.Path:
        Path to the Bpod directory

    """
    default_path_file = get_default_path_file()

    if default_path_file:
        return default_path_file

    return Path.home() / "Documents/Bpod"
    # If the default path isn't saved to disk, return the default
