"""main entry point for bpod-rig"""

import logging
from pydantic import ValidationError

from bpod_rig.config import utils
from bpod_rig.config.system_settings import SystemPaths
from bpod_rig.IO import default_setup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    ### Everything below is subject to change and is for testing purposes only
    logger.info("Initializing bpod-rig!")

    bpod_dir_verified = False  # Let's put this in a BpodSystem class later

    # Initialize Setup
    bpod_directory = default_setup.get_bpod_directory_path()

    try:
        system_paths = SystemPaths(base_dir=bpod_directory)
        bpod_dir_verified = True
    except ValidationError as ve:
        logger.error("Error initializing system paths: %s", exc_info=ve)

    if not bpod_dir_verified:
        logger.info("The Bpod directory at %s failed to verify!"
                    " This could be due to a partially initialized folder structure or "
                    "improper file path!", bpod_directory)
        response = input(f"Would you like to re-create the default folder structure at {bpod_directory}? (y/n)")

        if response == "y":
            bpod_directory = default_setup.create_default_directories()

    # Populate this machine's folders with the default config and calibration files.
    default_setup.copy_default_files(bpod_directory)

    inital_system_config = utils.init_system_configuration(
        bpod_directory
    )

    result = utils.save_system_configuration(inital_system_config)

if __name__ == "__main__":
    main()
