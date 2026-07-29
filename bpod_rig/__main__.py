"""main entry point for bpod-rig."""

import logging
from logging.config import dictConfig
from typing import Annotated

import typer
from pydantic import ValidationError

from bpod_rig.cli.prompts import prompt_for_path, yes_no_prompt
from bpod_rig.cli.protocols import app as protocols_app
from bpod_rig.cli.test import app as test_app
from bpod_rig.config import utils
from bpod_rig.config.bpod_paths import BpodPaths_2
from bpod_rig.defaults import DEFAULT_BPOD_PATH, SYSTEM_CONFIG_FILE
from bpod_rig.IO import startup
from bpod_rig.log import BpodLogger, get_log_config, get_logger
from config import system_settings, SystemSettings

DEBUG = True

# Set up logging here
logging_config = get_log_config(debug=DEBUG)
dictConfig(logging_config)
logging.setLoggerClass(BpodLogger)
logger: BpodLogger = get_logger(__name__)

app = typer.Typer(no_args_is_help=True)
app.add_typer(protocols_app, name="protocols")
app.add_typer(test_app, name="test")


@app.command()
def init() -> int:
    """Initialize the Bpod Rig on this system."""
    ### Everything below is subject to change and is for testing purposes only
    logger.info("Starting bpod-rig!")

    # Let's put this in a BpodSystem class later
    bpod_dir_verified = False
    reinitialize = False
    bpod_path = None
    system_paths: BpodPaths_2 | None = None
    sys_settings: SystemSettings | None = None

    ### Are we running from a supported environment?
    environment_allowed = startup.check_supported_environment()
    if not environment_allowed:
        logger.error("bpod-rig is NOT running inside a virtual environment!\n",
                     "bpod-rig must be run from inside a virtual environment!\n"
                     "Please visit the bpod-rig wiki at"
                     " https://bpod-rig.sanworks.io/installation for installation"
                     "instructions. Exiting...")
        return -1
    else:
        logger.debug("Virtual environment verified!")

    ### Has Bpod been initialized on this system before? ###
    system_initialized = startup.check_system_is_initialized()
    if not system_initialized:
        logger.info("Initializing Bpod Rig...")
        logger.debug("System is not initialized!")
        # We have no reference to paths, did the user provide a path some other way?
        # TODO: accept bpod_dir via CLI or ENV
    else:
        logger.debug(
            "System configuration file exists."
            " Attempting to read paths from configuration file"
        )
        # System has already been initialized
        try:
            # No reason to load this twice if it exists
            sys_settings = system_settings.load_system_configuration(SYSTEM_CONFIG_FILE)
            system_paths = sys_settings.paths
        except ValidationError:
            logger.exception(
                "Configuration file at %s failed to validate! "
                "Cannot read the Bpod Directories from existing configuration!",
                SYSTEM_CONFIG_FILE,
            )
            return -1

    if system_paths is None:
        # This is the first time initializing the system; override default path?
        logger.info("Creating Bpod directory...")
        override_directory = yes_no_prompt(
            f"Bpod has not been initialized on this system! "
            f"Would you like to override the default path {DEFAULT_BPOD_PATH}?"
        )
        if override_directory is None:
            logger.info("User aborted when overriding default path! Exiting...")
            return -1
        if override_directory:
            logger.debug("User is going to override the path!")
            bpod_path = prompt_for_path(
                "Please enter the path to create the Bpod directory", must_exist=False
            )
            if bpod_path is None:
                logger.info("User aborted when overriding default path! Exiting...")
                return -1
        else:
            # If the user does not want to overwrite the default directory
            bpod_path = DEFAULT_BPOD_PATH

        # Instantiate BpodPaths_2 object to generate subdirectories
        system_paths = BpodPaths_2.create(base_dir=bpod_path)
    else:
        bpod_path = system_paths.base_dir

    logger.info("Bpod path set to: %s", bpod_path)

    ## Verify Bpod Folder Structure ##
    if system_initialized:
        # Let's only verify the directory if Bpod has already been
        # initialized on this system
        bpod_dir_verified = system_paths.verify()

        # Verification Failed
        if not bpod_dir_verified:
            logger.info(
                "The Bpod directory at %s failed to verify!"
                " This could be due to a partially initialized folder structure or "
                "improper file path!",
                bpod_path,
            )
            reinitialize = yes_no_prompt(
                f"Would you like to (re)initialize {bpod_path} as the base"
                f" Bpod directory?"
            )

    if reinitialize or not system_initialized:
        # We will (re) create the Bpod directories if the system isn't initialized
        # or something went wrong and we need to reinitialize
        logger.info("Initializing Bpod directory at %s", bpod_path)
        bpod_path = startup.create_default_directories(bpod_path)
        bpod_dir_verified = True

        copy_default = yes_no_prompt(
            f"Would you like to copy the default protocols"
            f" and calibration files to {bpod_path}"
        )
        if copy_default:
            startup.copy_default_files(bpod_path)

    if bpod_dir_verified:
        logger.debug("System paths at %s verified", bpod_path)
    else:
        logger.error("No valid Bpod directory! Shutting down.")
        raise RuntimeError("Bpod directory verification failed after initialization!")

    # We have a logging directory!
    logger.swap_stream(system_paths.log_dir)

    # Now we are initialized, and directories are validated
    # Create and save the config.json file if this is a first install!
    if sys_settings is None:
        sys_settings = SystemSettings.create(paths=system_paths)
        sys_settings.save_system_configuration()

    return 0


@app.command()
def run(
    protocol: Annotated[
        str,
        typer.Argument(
            ..., help="Name of the protocol file, or path to the protocol file"
        ),
    ],
    subject: Annotated[str, typer.Argument(..., help="Subject identifier")],
    port: Annotated[str | None, typer.Option(..., help="COM port for the Bpod")] = None,
    serial_number: Annotated[
        int | None, typer.Option(..., help="Serial number of the Bpod")
    ] = None,
    protocol_args: Annotated[
        str | None,
        typer.Option(..., help="Additional arguments for the protocol"),
    ] = None,
) -> None:
    """Run a protocol on the Bpod Rig.

    A protocol can be specified by its name if in protocol folder, or by a path to the
    protocol file.
    """
    raise NotImplementedError()


def main() -> None:
    init()

if __name__ == "__main__":
    main()
