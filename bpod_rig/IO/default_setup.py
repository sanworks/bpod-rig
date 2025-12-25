"""Module to create the default Bpod user directory and associated subdirs."""

import logging
import shutil
from pathlib import Path

import platformdirs
from pydantic import ValidationError

from bpod_rig.examples import calibration, settings
from bpod_rig.config import utils
from bpod_rig.IO import cli_io

DEFAULT_SUBDIRS = ["Config", "Calibration", "Protocols", "Data", "Logs"]
DEFAULT_DIR_NAME = "Bpod"

SYSTEM_CONFIG_DIR = platformdirs.user_config_path(DEFAULT_DIR_NAME)
SYSTEM_CONFIG_FILE = SYSTEM_CONFIG_DIR / "system_config.json"
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


def get_bpod_dir_from_system() -> Path | None:
    """Attempts to get the Bpod directory path from the system configuration file

    Checks to see if the system configuration directory exists, if so, check to see
    if there is a system configuration file. If there is attempt to read the Bpod
    directory path from the configuration file.

    Returns
    -------
    pathlib.Path
        Path to the Bpod directory read from the system configuration file

    None
        If the system configuration directory does not exist, the configuration file
        does not exist, or there is an error reading from the file, return None

    """

    if SYSTEM_CONFIG_DIR.exists():
        # Check if the system configuration directory exists
        logger.debug("Found system config directory: %s", SYSTEM_CONFIG_DIR)
        if SYSTEM_CONFIG_FILE.exists():
            # Check if the system configuration file exists
            logger.debug(
                "system_config.json found! Attempting to read Bpod directory path!"
            )
            try:
                # Attempt to load and read path from system configuration file
                system_settings = utils.load_system_configuration(SYSTEM_CONFIG_FILE)
                return system_settings.paths.base_dir
            except ValidationError as e:
                logger.error(
                    "Configuration file at %s failed to validate!",
                    SYSTEM_CONFIG_FILE,
                    exc_info=e,
                )
            logger.error(
                "Unable to read Bpod directory path from system configuration file!"
            )
        else:
            logger.warning(
                "No system_config.json found! Has system been fully initialized?"
            )
    else:
        logger.warning("No system config directory found!")

    return None


def check_system_is_initialized() -> bool:
    """Checks whether Bpod has been initialized on this system before

    If the system configuration directory does not exist, the system has not been initialized
    If the system configuration directory exists, but the system_config.json file
    does not exist, the system likely has only been partially initialized and needs to
    be reinitialized.

    Returns
    ------
    bool
        True if system is initialized, False otherwise
    """

    if SYSTEM_CONFIG_DIR.exists():
        logger.debug("System configuration directory found: %s", SYSTEM_CONFIG_DIR)
        if SYSTEM_CONFIG_FILE.exists():
            logger.debug("System configuration file found: %s", SYSTEM_CONFIG_FILE)
            return True
    return False


def get_bpod_directory() -> Path:
    bpod_path = get_bpod_dir_from_system()

    if bpod_path is None:
        logger.info("Unable to get Bpod path from system configuration!")
        bpod_path = DEFAULT_BPOD_PATH

    return bpod_path
