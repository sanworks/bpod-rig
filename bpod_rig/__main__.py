"""main entry point for bpod-rig."""

import logging
from pydantic import ValidationError

from bpod_rig.config import utils
from bpod_rig.config.system_settings import BpodDir
from bpod_rig.IO import startup, cli_io
from bpod_rig.defaults import DEFAULT_BPOD_PATH, SYSTEM_CONFIG_DIR, SYSTEM_CONFIG_FILE
from config import system_settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
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
        logging.debug(
            "System is not initialized. Creating system config dir [%s]",
            SYSTEM_CONFIG_DIR
        )
        # Create the system configuration directory
        try:
            SYSTEM_CONFIG_DIR.mkdir(exist_ok=True, parents=True)
        except (IOError, OSError) as e:
            logger.error(
                "Unable to create the system configuration directory: %s Exiting...",
                SYSTEM_CONFIG_DIR,
                exc_info=e
            )
            return
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
            return -1

    if bpod_path is None:
        # This is the first time initializing the system; override default path?
        override_directory = cli_io.yes_no_prompt(
            f"Bpod has not been initialized on this system! "
            f"Would you like to override the default path {DEFAULT_BPOD_PATH}?"
        )
        if override_directory:
            logger.debug("User is going to override the path!")
            bpod_path = cli_io.prompt_for_path(
                "Please enter the path to create the Bpod directory"
            )
        else:
            bpod_path = DEFAULT_BPOD_PATH

    logger.info("Bpod path set to: %s", bpod_path)

    ## Verify Bpod Folder Structure ##

    # Instantiate SystemPaths object to generate subdirectories
    system_paths = BpodDir(base_dir=bpod_path)
    bpod_dir_verified = system_paths.verify()

    # Verification Failed
    if not bpod_dir_verified:
        logger.info(
            "The Bpod directory at %s failed to verify!"
            " This could be due to a partially initialized folder structure or "
            "improper file path!",
            bpod_path,
        )
        reinitialize = cli_io.yes_no_prompt(
            f"Would you like to (re)initialize {bpod_path} as the base"
            f" Bpod directory?"
        )

    if reinitialize or not system_initialized:
        logging.info("Initializing Bpod directory at %s", bpod_path)
        bpod_path = startup.create_default_directories(bpod_path)
        bpod_dir_verified = True

        copy_default = cli_io.yes_no_prompt(
            f"Would you like to copy the default protocols and calibration files to {bpod_path}"
        )
        if copy_default:
            startup.copy_default_files(bpod_path)

    if bpod_dir_verified:
        logging.debug("System paths at %s verified", bpod_path)
    else:
        logger.error("No valid Bpod directory! Shutting down.")
        return


    initial_system_config = utils.init_system_configuration(bpod_path)
    user_config_path = initial_system_config.save_system_configuration()
    system_config_path = initial_system_config.save_system_configuration(
        save_dir_override=SYSTEM_CONFIG_DIR
    )

if __name__ == "__main__":
    main()
