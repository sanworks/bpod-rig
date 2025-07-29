"""main entry point for bpod-rig"""
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing bpod-rig!")

if __name__ == "__main__":
    main()
