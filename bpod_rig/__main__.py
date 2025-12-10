"""main entry point for bpod-rig"""

import logging

from bpod_rig.config import utils
from bpod_rig.IO import default_setup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    ### Everything below is subject to change and is for testing purposes only

    logger.info("Initializing bpod-rig!")
    # Setup folders. "EMU" is the USB serial port argument for the emulator.
    # create_default_directories() is called later to add folders for each FSM on the PC
    bpod_directory = default_setup.create_default_directories()

    # Populate this machine's folders with the default config and calibration files.
    default_setup.copy_default_files(bpod_directory)

    inital_system_config = utils.init_system_configuration(
        bpod_directory
    )

    result = utils.save_system_configuration(inital_system_config)

if __name__ == "__main__":
    main()
