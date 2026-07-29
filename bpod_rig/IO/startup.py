"""Module to create the default Bpod user directory and associated subdirs."""

from pathlib import Path

from bpod_rig import log
from bpod_rig.defaults import (
    _BPOD_RIG_PYTHON,
    _SYSTEM_PYTHON,
    DEFAULT_SUBDIRS,
    SYSTEM_CONFIG_FILE,
)
from bpod_rig.examples.copy import copy_examples

logger = log.get_logger(__name__)


def create_default_directories(bpod_directory_path: Path) -> Path:
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
        logger.debug("Creating default Bpod user directory in %s", bpod_directory_path)
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
        else:
            logger.debug("Subdirectory [%s] already exists", subdir)

    if is_new_install:
        logger.info("Bpod user directory initialized to %s", bpod_directory_path)

    return bpod_directory_path


def copy_default_files(bpod_folder_path: Path, *, override: bool = False) -> None:
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

    copy_examples("calibration", calibration_dir, override_contents=override)
    copy_examples("settings", settings_dir, override_contents=override)


def check_system_is_initialized() -> bool:
    """Checks whether Bpod has been initialized on this system before.

    If the system configuration file does not exist, the system has
    not been initialized.

    Returns
    -------
    bool
        True if system is initialized, False otherwise
    """
    if SYSTEM_CONFIG_FILE.exists():
        logger.debug("System configuration file found: %s", SYSTEM_CONFIG_FILE)
        return True
    return False


def check_supported_environment() -> bool:
    """Checks whether bpod-rig is running from a supported environment.

    bpod-rig is only supported when running inside a virtual environment. Using the
    system python installation is not supported!

    Returns
    -------
    bool
        True if bpod-rig is running inside a virtual environment, False otherwise
    """

    if _SYSTEM_PYTHON == _BPOD_RIG_PYTHON:
        logger.debug("bpod-rig interpreter: %s \n"
                     "system interpreter: %s \n")
        return False
    return True
