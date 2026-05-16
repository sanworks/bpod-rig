"""Module to create the default Bpod user directory and associated subdirs."""

import logging
from pathlib import Path
from typing import Optional

import typer
from pydantic import ValidationError

from bpod_rig.config import system_settings
from bpod_rig.defaults import (
    DEFAULT_BPOD_PATH,
    DEFAULT_SUBDIRS,
    SYSTEM_CONFIG_DIR,
    SYSTEM_CONFIG_FILE,
)
from bpod_rig.examples.copy import copy_examples
from bpod_rig.IO import cli_io, startup

logger = logging.getLogger(__name__)


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

    copy_examples("calibration", calibration_dir, override_contents=override)
    copy_examples("settings", settings_dir, override_contents=override)


def get_bpod_dir_from_system() -> Path | None:
    """Attempts to get the Bpod directory path from the system configuration file.

    Checks to see if the system configuration directory exists, if so, check to see
    if there is a system configuration file. If there is attempt to read the Bpod
    directory path from the configuration file.

    Returns
    -------
    pathlib.Path
        Path to the Bpod directory read from the system configuration file
    """
    # Attempt to load and read path from system configuration file
    sys_settings = system_settings.load_system_configuration(SYSTEM_CONFIG_FILE)
    return sys_settings.paths.base_dir


def check_system_is_initialized() -> bool:
    """Checks whether Bpod has been initialized on this system before.

    If the system configuration directory does not exist, the system has
    not been initialized
    If the system configuration directory exists, but the system_config.json file
    does not exist, the system likely has only been partially initialized and needs to
    be reinitialized.

    Returns
    -------
    bool
        True if system is initialized, False otherwise
    """
    if SYSTEM_CONFIG_DIR.exists():
        logger.debug("System configuration directory found: %s", SYSTEM_CONFIG_DIR)
        if SYSTEM_CONFIG_FILE.exists():
            logger.debug("System configuration file found: %s", SYSTEM_CONFIG_FILE)
            return True
    return False


class InitializeBpodSystemOperation:
    """Create filesystem structure.

    Steps
    1. Check if system is already initialized
    2. Prompt for or use provided bpod_path
    3. Create/verify directory structure
    4. Optionally copy example files
    5. Save system configuration


    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._system_initialized = False
        self._bpod_dir_verified = False
        self.bpod_path: Path | None = None
        self._logger = logger or logging.getLogger(__name__)

    def execute(self):
        self._initialize_system_config()
        self._determine_bpod_path()
        if True:
            self._reinitialize_bpod_directory(Path(""))
        self._swap_log_stream(Path(""))

    def _initialize_system_config(self) -> None:
        if check_system_is_initialized():
            self._logger.info("System is already initialized.")
            self._system_initialized = True
            return
        logger.info("Initializing Bpod Rig...")
        logger.debug(
            "System is not initialized. Creating system config dir [%s]",
            SYSTEM_CONFIG_DIR,
        )
        # Create the system configuration directory
        SYSTEM_CONFIG_DIR.mkdir(exist_ok=True, parents=True)

    def _determine_bpod_path(self) -> None:
        try:
            self.bpod_path = startup.get_bpod_dir_from_system()
        except ValidationError as e:
            logger.error(
                "Configuration file at %s failed to validate! "
                "Cannot read the Bpod Directory from existing configuration!",
                SYSTEM_CONFIG_FILE,
                exc_info=e,
            )
            raise e
        if self.bpod_path is not None:
            return

        # bpod_path does not exist

        logger.info("Creating Bpod directory...")
        override_directory = typer.confirm(
            f"Bpod has not been initialized on this system! "
            f"Would you like to override the default path {DEFAULT_BPOD_PATH}?"
        )
        override_directory = cli_io.yes_no_prompt(
            f"Bpod has not been initialized on this system! "
            f"Would you like to override the default path {DEFAULT_BPOD_PATH}?"
        )
        if override_directory is None:
            logger.info("User aborted when overriding default path! Exiting...")
            return
        if override_directory:
            logger.debug("User is going to override the path!")
            bpod_path = cli_io.prompt_for_path(
                "Please enter the path to create the Bpod directory"
            )
            if bpod_path is None:
                logger.info("User aborted when overriding default path! Exiting...")
                return
        else:
            # If the user does not want to overwrite the default directory
            bpod_path = DEFAULT_BPOD_PATH

    def _reinitialize_bpod_directory(self, bpod_path: Path) -> None:
        pass

    def _swap_log_stream(self, new_log_path: Path) -> None:
        pass
