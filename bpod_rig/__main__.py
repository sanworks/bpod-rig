"""main entry point for bpod-rig."""

import logging
from logging.config import dictConfig
from typing import Annotated, cast

import typer
from pydantic import ValidationError

from bpod_rig.cli.prompts import prompt_for_path, yes_no_prompt
from bpod_rig.cli.protocols import app as protocols_app
from bpod_rig.cli.test import app as test_app
from bpod_rig.config import startup, utils
from bpod_rig.config.system_settings import BpodDir
from bpod_rig.defaults import DEFAULT_BPOD_PATH, SYSTEM_CONFIG_DIR, SYSTEM_CONFIG_FILE
from bpod_rig.log import BpodLogger, get_log_config

DEBUG = True

# Set up logging here
logging_config = get_log_config(DEBUG)
dictConfig(logging_config)
logging.setLoggerClass(BpodLogger)
logger: BpodLogger = cast(BpodLogger, logging.getLogger(__name__))

app = typer.Typer(no_args_is_help=True)
app.add_typer(protocols_app, name="protocols")
app.add_typer(test_app, name="test")


@app.command()
def init():
    from bpod_rig.config.startup import CLIStartupChoiceAdapter, initialize_bpod_system

    result = initialize_bpod_system(
        choices=CLIStartupChoiceAdapter(),
        default_bpod_path=DEFAULT_BPOD_PATH,
        logger=logger,
    )
    if result.state != startup.InitState.COMPLETED:
        logger.error("Initialization failed: %s", result.message)
        typer.Exit(code=-1)
        # raise RuntimeError(f"Initialization failed: {result.message}")


@app.command()
def init_old():
    """Initialize the Bpod Rig on this system."""
    ### Everything below is subject to change and is for testing purposes only
    logger.info("Starting bpod-rig!")
    # Let's put this in a BpodSystem class later
    bpod_dir_verified = False
    reinitialize = False
    system_initialized = False
    bpod_path = None

    ### Has Bpod been initialized on this system before? ###
    system_initialized = startup.check_system_is_initialized()
    if not system_initialized:
        logger.info("Initializing Bpod Rig...")
        logger.debug(
            "System is not initialized. Creating system config dir [%s]",
            SYSTEM_CONFIG_DIR,
        )
        # Create the system configuration directory
        try:
            SYSTEM_CONFIG_DIR.mkdir(exist_ok=True, parents=True)
        except (IOError, OSError) as e:
            logger.error(
                "Unable to create the system configuration directory: %s Exiting...",
                SYSTEM_CONFIG_DIR,
                exc_info=e,
            )
            return -1
    else:
        logger.debug(
            "System configuration directory is already initialized."
            " Attempting to read bpod_path from configuration file"
        )
        # System has already been initialized
        try:
            bpod_path = startup.get_bpod_dir_from_system()
        except ValidationError as e:
            logger.error(
                "Configuration file at %s failed to validate! "
                "Cannot read the Bpod Directory from existing configuration!",
                SYSTEM_CONFIG_FILE,
                exc_info=e,
            )
            raise

    if bpod_path is None:
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

    logger.info("Bpod path set to: %s", bpod_path)

    ## Verify Bpod Folder Structure ##

    # Instantiate BpodDir object to generate subdirectories
    system_paths = BpodDir.create(base_dir=bpod_path)
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
        startup.create_default_directories(bpod_path)
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
        raise

    logger.swap_stream(system_paths.log_dir)

    initial_system_config = utils.init_system_configuration(bpod_path)
    user_config_path = initial_system_config.save_system_configuration()  # noqa: F841
    system_config_path = initial_system_config.save_system_configuration(  # noqa: F841
        save_dir_override=SYSTEM_CONFIG_DIR
    )

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
):
    """Run a protocol on the Bpod Rig.

    A protocol can be specified by its name if in protocol folder, or by a path to the
    protocol file.
    """
    raise NotImplementedError()


def main():
    app()


if __name__ == "__main__":
    main()
