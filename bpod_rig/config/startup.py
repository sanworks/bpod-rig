"""Module to create the default Bpod user directory and associated subdirs."""

import logging
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from bpod_rig.cli.prompts import prompt_for_path, yes_no_prompt
from bpod_rig.config import system_settings, utils
from bpod_rig.defaults import (
    DEFAULT_SUBDIRS,
    SYSTEM_CONFIG_FILE, _SYSTEM_PYTHON, _BPOD_RIG_PYTHON,
)
from bpod_rig.examples.copy import copy_examples
from bpod_rig.log import BpodLogger
from config import SystemSettings
from config.bpod_paths import BpodPaths_2

logger = logging.getLogger(__name__)


class InitState(Enum):
    """Possible states during initialization process."""

    NOT_INITIALIZED = auto()
    """
    The system has not been initialized.
    This is the default state before any initialization logic runs.
    """
    INITIALIZED_VALID = auto()
    """The system has been initialized and the Bpod directory is valid."""
    INITIALIZED_INVALID = auto()
    """The system has been initialized but the Bpod directory is invalid."""
    ABORTED = auto()
    """Process was aborted by the user."""
    COMPLETED = auto()
    """Process completed successfully, new Bpod directory created."""
    SKIPPED = auto()
    """Process was skipped because the system was already initialized and valid."""
    FAILED = auto()
    """Process failed."""


@dataclass
class InitResult:
    """Representation of initialization process outcome."""

    state: InitState
    """The final state of the initialization process."""
    message: list[str] | str
    """
    An optional message providing additional information about the
    initialization result (to be displayed to the user).
    """
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


class StartupChoiceProtocol(Protocol):
    """Each of the possible decisions during system initialization."""

    def choose_override_path(self, default_path: Path) -> Path | None:
        """
        When the system is not initialized or is being reinitialized, ask the user if
        they want to override the default path and if so, prompt them to enter a path.
        Return the chosen path or None if the user aborts.
        """
        ...

    def choose_reinitialize_invalid_system_config(
        self, invalid_path: Path
    ) -> bool | None:
        """
        When the system configuration file is found but fails to load, ask the user if
        they want to reinitialize.
        Return True if they want to reinitialize, False if they want to keep the
        existing config, or None if they abort.
        """
        ...

    def choose_reinitialize_invalid_dir(self, invalid_path: Path) -> bool | None:
        """
        When the system is initialized but the Bpod directory fails verification, ask
        the user if they want to reinitialize.
        Return True if they want to reinitialize, False if they want to keep the
        invalid directory, or None if they abort.
        """
        ...

    def choose_copy_defaults(self, bpod_path: Path) -> bool | None:
        """
        Ask the user if they want to copy default files to the given Bpod path.
        Return True if they want to copy defaults, False if not, or None if they abort.
        """
        ...


class CLIStartupChoiceAdapter(StartupChoiceProtocol):
    def choose_override_path(self, default_path: Path) -> Path | None:
        override = yes_no_prompt(
            f"Override default path {default_path}?"
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

    def choose_reinitialize_invalid_system_config(
        self, invalid_path: Path
    ) -> bool | None:
        return yes_no_prompt(
            f"The system configuration file at {invalid_path} is invalid. Reinitialize?"
        )

    def choose_copy_defaults(self, bpod_path: Path) -> bool | None:
        return yes_no_prompt(
            f"Copy default protocols and calibration files to {bpod_path}?"
        )


def initialize_bpod_system(  # noqa: PLR0911
    choices: StartupChoiceProtocol, default_bpod_path: Path, logger: BpodLogger
) -> InitResult:
    """Initialize the Bpod system on this machine.


    Parameters
    ----------
    choices : StartupChoiceProtocol
        An object that implements the StartupChoiceProtocol to handle
        user choices during initialization.
    default_bpod_path : pathlib.Path
        The default path to the Bpod directory to suggest during initialization.
    logger : BpodLogger
        A logger instance to use for logging during initialization.

    Returns
    -------
    InitResult
        An object representing the outcome of the initialization process, including
        the final state and any messages,
    """
    logger.info("Initializing bpod-rig")

    system_paths: BpodPaths_2 | None = None
    bpod_path: Path | None = None
    reinitialize: bool = False

    try:
        environment_allowed = check_supported_environment()
        if not environment_allowed:
            return InitResult(
                state=InitState.FAILED,
                message=["bpod-rig is NOT running inside a virtual environment!\n"
                "bpod-rig must be run from inside a virtual environment!\n"
                "Please visit the bpod-rig wiki at"
                " https://bpod-rig.sanworks.io/installation for installation"
                "instructions. Exiting..."]
            )
        else:
            logger.debug("Virtual environment verified!")

        initialized = check_system_is_initialized()

        if initialized:
            # We found the system config file, can we read it?
            logger.debug("Attempting to read system configuration from disk")
            try:
                # No reason to load this twice if it exists
                sys_settings = system_settings.load_system_configuration(SYSTEM_CONFIG_FILE)
                system_paths = sys_settings.paths
                bpod_path = system_paths.base_dir
            except (TypeError, ValidationError):
                # Uh oh, we cannot load the system settings
                logger.warning("Unable to load system configuration from disk!")
                reinitialize = choices.choose_reinitialize_invalid_system_config(
                    SYSTEM_CONFIG_FILE
                )
                if reinitialize is None:
                    return InitResult(
                        state=InitState.ABORTED,
                        message="User aborted reinitialize decision "
                        "for invalid system config.",
                        config_path=SYSTEM_CONFIG_FILE,
                    )
                if not reinitialize:
                    return InitResult(
                        state=InitState.INITIALIZED_INVALID,
                        message="System configuration file is invalid "
                        "and user declined reinitialization.",
                        config_path=SYSTEM_CONFIG_FILE,
                    )

            # Time to verify our directory structure
            configuration_is_valid = system_paths.verify()

            if not configuration_is_valid:
                logger.info("Bpod directory at %s failed verification.", bpod_path)
                reinit = choices.choose_reinitialize_invalid_dir(bpod_path)
                if reinit is None:
                    return InitResult(
                        state=InitState.ABORTED,
                        message="User aborted reinitialize decision.",
                        bpod_path=bpod_path,
                    )
                if not reinit:
                    return InitResult(
                        state=InitState.INITIALIZED_INVALID,
                        message="Directory invalid and reinitialize declined.",
                        bpod_path=bpod_path,
                    )
                else:
                    logger.debug("Reinitializing bpod directory to: %s", reinit)
            else:
                # Update logging path
                logger.swap_stream(system_paths.log_dir)
                return InitResult(
                    state=InitState.SKIPPED,
                    message="Bpod is already initialized and valid.",
                    bpod_path=bpod_path,
                )
        else:
            logger.debug("Checking for other sources of bpod_dir")
            # We have no reference to paths, did the user provide a path some other way?
            # Either way this is a new install
            # TODO: accept bpod_dir via CLI or ENV.
            # pseudocode: if external_bpod_dir_path -> create system_paths


        if system_paths is None or reinitialize:
            # If system_paths is None that means we could not load anything (new install)
            # If configuration_is_valid is false, that means we failed to verify an existing
            # Directory and the user decided to reinitialize
            if reinitialize:
                logger.info("Reinitializing bpod-rig")
                # We couldn't read the bpod directory path, but the user wants to
                # reinitialize the system
            else:
                logger.info("Initializing a new bpod-rig install!")
                # System was never initialized

            # Does the user want to override the paths?
            base_directory = choices.choose_override_path(
                default_bpod_path,
            )
            if base_directory is None:
                return InitResult(
                    state=InitState.ABORTED,
                    message="User aborted path selection.",
                )

            system_paths = BpodPaths_2.create(base_dir=base_directory)
            bpod_path = system_paths.base_dir

            # If the user has chosen to reinitialise the choice is to copy the data
            choices.choose_copy_defaults = lambda bpod_path: True  # noqa: ARG005
            copied_defaults = _initialize_system_config_dir(
                choices, bpod_path, logger
            )

            logger.swap_stream(system_paths.log_dir)
            initial_system_config = SystemSettings.create(system_paths)
            config_path = initial_system_config.save_system_configuration()
            return InitResult(
                state=InitState.COMPLETED,
                message="Initialization successful.",
                bpod_path=bpod_path,
                copied_defaults=copied_defaults,
                config_path=config_path,
            )
    except Exception as exc:
        logger.exception("Unexpected error during initialization")
        return InitResult(
            state=InitState.FAILED,
            message="Unexpected error occurred: " + str(exc),
        )


def _initialize_system_config_dir(
    choices: StartupChoiceProtocol, bpod_path: Path, logger: logging.Logger
) -> bool:
    """Fill the directory with default files and folders, if the user chooses to."""
    create_default_directories(bpod_path)
    copy_default = choices.choose_copy_defaults(bpod_path)
    if copy_default:
        logger.info("Chose to copy default files to %s", bpod_path)
        copy_default_files(bpod_path)
        return True
    logger.info("Chose not to copy default files to %s", bpod_path)
    return False


def create_default_directories(bpod_directory_path: Path) -> None:
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

    """
    if not bpod_directory_path.exists():
        logger.debug("Creating default Bpod user directory in %s", bpod_directory_path)
        bpod_directory_path.mkdir(parents=True, exist_ok=True)
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
