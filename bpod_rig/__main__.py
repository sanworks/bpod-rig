"""main entry point for bpod-rig"""

import logging

from bpod_rig.IO import default_setup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    logger.info("Initializing bpod-rig!")
    bpod_directory = default_setup.create_default_directories()
    default_setup.copy_default_files(bpod_directory)
    logger.info("Bpod directory initialized to %s", bpod_directory)


if __name__ == "__main__":
    main()
