"""Module to create the default Bpod user directory and associated subdirs."""

import logging
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Protocol

from bpod_rig.cli.prompts import prompt_for_path, yes_no_prompt
from bpod_rig.config import system_settings, utils
from bpod_rig.defaults import (
    DEFAULT_SUBDIRS,
    SYSTEM_CONFIG_DIR,
    SYSTEM_CONFIG_FILE,
)
from bpod_rig.examples.copy import copy_examples
from bpod_rig.log import BpodLogger

logger = logging.getLogger(__name__)


class InitState(Enum):
    """Possible states during initialization process."""

    NOT_INITIALIZED = auto()
    """The system has not been initialized. This is the default state before any initialization logic runs."""
    INITIALIZED_VALID = auto()
    """The system has been initialized and the Bpod directory is valid."""
    INITIALIZED_INVALID = auto()
    """The system has been initialized but the Bpod directory is invalid."""
    ABORTED = auto()
    """The initialization process was aborted by the user."""
    COMPLETED = auto()
    """The initialization process completed successfully."""
    FAILED = auto()
    """The initialization process failed."""


@dataclass
class InitResult:
    """Representation of initialization process outcome."""

    success: bool
    """Whether the initialization process completed successfully."""
    state: InitState
    """The final state of the initialization process."""
    message: list[str] | str
    """An optional message providing additional information about the initialization result."""
    details: dict | None = None
    """Any additional details about the initialization result."""
    bpod_path: Path | None = None
    """The path to the Bpod directory that was initialized or verified."""
    copied_defaults: bool = False
    """Whether default files were copied to the Bpod directory."""
    user_config_path: Path | None = None
    """The path to the saved user configuration file, if applicable."""
    system_config_path: Path | None = None
    """The path to the saved system configuration file, if applicable."""



class StartupChoicePort(Protocol):
    """Each of the possible decisions during system initialization."""

    def choose_path_first_init(self, default_path: Path) -> Path | None:
        """When the system is not initialized, ask the user if they want to override the default path and if so, prompt them to enter a path. Return the chosen path or None if the user aborts."""
        ...

    def choose_reinitialize_invalid_dir(self, invalid_path: Path) -> bool | None:
        """When the system is initialized but the Bpod directory fails verification, ask the user if they want to reinitialize. Return True if they want to reinitialize, False if they want to keep the invalid directory, or None if they abort."""
        ...

    def choose_copy_defaults(self, bpod_path: Path) -> bool | None:
        """Ask the user if they want to copy default files to the given Bpod path. Return True if they want to copy defaults, False if not, or None if they abort."""
        ...


class CLIStartupChoiceAdapter(StartupChoicePort):
    def choose_path_first_init(self, default_path: Path) -> Path | None:
        override = yes_no_prompt(
            f"Bpod has not been initialized. Override default path {default_path}?"
        )
        if override is None:
            return None
        if not override:
            return default_path
        return prompt_for_path(
            "Please enter the path to create the Bpod directory", must_exist=False
        )

    def choose_reinitialize_invalid_dir(self, invalid_path: Path) -> bool | None:
        return yes_no_prompt(
            f"The Bpod directory at {invalid_path} failed verification. Reinitialize?"
        )

    def choose_copy_defaults(self, bpod_path: Path) -> bool | None:
        return yes_no_prompt(
            f"Copy default protocols and calibration files to {bpod_path}?"
        )

class InitService:
    """Service class to handle Bpod initialization logic."""

    def __init__(
        self,
        choices: StartupChoicePort,  # this is "Port" because it's an interface that can be implemented by different adapters (e.g. CLI, GUI)
        default_bpod_path: Path,
        logger: BpodLogger,
    ):
        self.choices = choices
        self.default_bpod_path = default_bpod_path
        self.logger = logger
        self.result = InitResult(
            success=False,
            state=InitState.NOT_INITIALIZED,
            message="Initialization not started.",
        )

    def run(self) -> InitResult:
        try:
            initialized = check_system_is_initialized()
            # todo: verify integ of system file
            if not initialized:
                if not self._ensure_system_config_dir_exists():
                    self.result.state = InitState.FAILED
                    self.result.message = "Failed to create system configuration directory. Check permissions and available disk space."
                    return self.result
                bpod_path = self.choices.choose_path_first_init(self.default_bpod_path)
                if bpod_path is None:
                    self.result.state = InitState.ABORTED
                    self.result.message = "User aborted path selection"
                    return self.result

                self._initialize_system_config_dir()
            else:
                bpod_path = get_bpod_dir_from_system()
                if bpod_path is None:
                    self.result.state = InitState.FAILED
                    self.result.message = "System is initialized but failed to read Bpod path from system configuration file."
                    return self.result

                system_paths = system_settings.BpodDir.create(base_dir=bpod_path)
                configuration_is_valid = system_paths.verify()
                if not configuration_is_valid:
                    reinit = self.choices.choose_reinitialize_invalid_dir(bpod_path)
                    if reinit is None:
                        self.result.state = InitState.ABORTED
                        self.result.bpod_path = bpod_path
                        self.result.message = "User aborted reinitialize decision"
                        return self.result
                    if not reinit:
                        self.result.success = False
                        self.result.state = InitState.INITIALIZED_INVALID
                        self.result.bpod_path = bpod_path
                        self.result.message = (
                            "Directory invalid and reinitialize declined"
                        )
                        return self.result

                    self._initialize_system_config_dir()
                else:
                    # System is already initialized and the directory is valid
                    self.result.copied_defaults = False

            # self.logger.swap_stream(system_paths.log_dir)
            initial_system_config = utils.init_system_configuration(bpod_path)
            user_config_path = initial_system_config.save_system_configuration()  # noqa: F841
            system_config_path = initial_system_config.save_system_configuration(  # noqa: F841
                save_dir_override=SYSTEM_CONFIG_DIR
            )
            self.result.success = True
            self.result.state = InitState.COMPLETED
            self.result.user_config_path = user_config_path
            self.result.system_config_path = system_config_path
            return self.result
        except Exception as exc:
            self.result.success = False
            self.result.state = InitState.FAILED
            self.result.message = "Unexpected error occurred: " + str(exc)
            return self.result

    def _initialize_system_config_dir(self) -> None:
        if self.result.bpod_path is None:
            raise ValueError(
                "Bpod path must be set before initializing system config directory"
            )
        bpod_path = self.result.bpod_path
        bpod_path = create_default_directories(bpod_path)
        self.result.bpod_path = bpod_path
        self.result.copied_defaults = self._maybe_copy_defaults(bpod_path)

    def _ensure_system_config_dir_exists(self) -> bool:
        try:
            SYSTEM_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        except (IOError, OSError) as exc:
            logger.error("Failed to create system configuration directory: %s", exc)
            return False
        return True

    def _maybe_copy_defaults(self, bpod_path: Path) -> bool:
        copy_default = self.choices.choose_copy_defaults(bpod_path)
        if copy_default:
            copy_default_files(bpod_path)
            return True
        return False


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
