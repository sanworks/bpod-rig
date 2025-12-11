"""main entry point for bpod-rig."""

import logging
from pydantic import ValidationError

from bpod_rig.config import utils
from bpod_rig.config.system_settings import SystemPaths
from bpod_rig.IO import default_setup, cli_io

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    ### Everything below is subject to change and is for testing purposes only
    logger.info("Initializing bpod-rig!")
    bpod_dir_verified = False  # Let's put this in a BpodSystem class later

    ### Find and verify the Bpod directory ###
    bpod_directory_path = default_setup.get_bpod_directory_path()

    # TODO: There needs to be an extra check to determine if there has been no
    # initialization performed. Will implement once I add in the path library
    # suggested by Steven as it will be a much more robust location to store files
    # for now we assume verification failure means broken OR never implemented -ACP

    try:
        system_paths = SystemPaths(base_dir=bpod_directory_path)
        bpod_dir_verified = utils.verify_bpod_directory(system_paths)
    except ValidationError as ve:
        logger.error("Error initializing system paths: %s", exc_info=ve)

    if not bpod_dir_verified:
        logger.info(
            "The Bpod directory at %s failed to verify!"
            " This could be due to a partially initialized folder structure or "
            "improper file path!",
            bpod_directory_path,
        )
        response = cli_io.yes_no_prompt(
            f"Would you like to (re)initialize {bpod_directory_path} as the base"
            f" Bpod directory?"
        )

        if response:
            logging.info("Initializing Bpod directory at %s", bpod_directory_path)
            bpod_directory_path = default_setup.create_default_directories(
                default_path_override=bpod_directory_path
            )
            # TODO: refactor this function to always require a path be given -ACP
            try:
                system_paths = SystemPaths(base_dir=bpod_directory_path)
                bpod_dir_verified = True
            except ValidationError as ve:
                logger.error("Error initializing system paths: %s", exc_info=ve)

            response = cli_io.yes_no_prompt(
                f"Would you like to copy the default protocols and calibration files to {bpod_directory_path}"
            )

            if response:
                default_setup.copy_default_files(bpod_directory_path)

    if bpod_dir_verified:
        logging.debug("System paths at %s verified", bpod_directory_path)
    else:
        logger.info("No valid Bpod directory! Shutting down.")
        return



    inital_system_config = utils.init_system_configuration(bpod_directory_path)

    result = utils.save_system_configuration(inital_system_config)


if __name__ == "__main__":
    main()
