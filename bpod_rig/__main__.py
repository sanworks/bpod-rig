"""main entry point for bpod-rig."""

import logging
from pydantic import ValidationError

from bpod_rig.config import utils
from bpod_rig.config.system_settings import SystemPaths
from bpod_rig.IO import default_setup, cli_io
from bpod_rig.defaults import DEFAULT_BPOD_PATH, SYSTEM_CONFIG_DIR, SYSTEM_CONFIG_FILE

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    ### Everything below is subject to change and is for testing purposes only
    logger.info("Starting bpod-rig!")
    bpod_dir_verified = False  # Let's put this in a BpodSystem class later

    ### Has Bpod been initialized on this system before? ###
    system_initialized = default_setup.check_system_is_initialized()
    if not system_initialized:
        # Time to do some initialization
        bpod_path = DEFAULT_BPOD_PATH
        override_directory = cli_io.yes_no_prompt(
            f"Bpod has not been initialized on this system! Would you like to override the default path {DEFAULT_BPOD_PATH}?"
        )
        if override_directory:
            logger.debug("User is going to override the path!")
            bpod_path = cli_io.prompt_for_path(
                "Please enter the path to create the Bpod directory"
            )

        # Create Bpod directories if the system was not initialized yet
        try:
            bpod_path = default_setup.create_default_directories(bpod_path)
        except (IOError, OSError) as e:
            logger.error(
                "Unable to create the Bpod directory: %s",
                bpod_path,
                exc_info=e
            )
            return

        # Create the system configuration directory
        try:
            SYSTEM_CONFIG_DIR.mkdir(exist_ok=True)
        except (IOError, OSError) as e:
            logger.error(
                "Unable to create the system configuration directory: %s",
                SYSTEM_CONFIG_DIR,
                exc_info=e
            )
            return
    else:
        # System has already been initialized
        bpod_path = default_setup.get_bpod_dir_from_system()

    ## Verify Bpod Folder Structure ##

    # Instantiate SystemPaths object to generate subdirectories
    system_paths = SystemPaths(base_dir=bpod_path)
    bpod_dir_verified = utils.verify_bpod_directory(system_paths)

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

        if reinitialize:
            logging.info("Initializing Bpod directory at %s", bpod_path)
            bpod_path = default_setup.create_default_directories(bpod_path)
            bpod_dir_verified = True

            copy_default = cli_io.yes_no_prompt(
                f"Would you like to copy the default protocols and calibration files to {bpod_path}"
            )
            if copy_default:
                default_setup.copy_default_files(bpod_path)

    if bpod_dir_verified:
        logging.debug("System paths at %s verified", bpod_path)
    else:
        logger.info("No valid Bpod directory! Shutting down.")
        return


    inital_system_config = utils.init_system_configuration(bpod_path)
    user_config_path = utils.save_system_configuration(inital_system_config)
    system_config_path = utils.save_system_configuration(
        inital_system_config,
        save_dir_override=SYSTEM_CONFIG_DIR
    )

if __name__ == "__main__":
    main()
