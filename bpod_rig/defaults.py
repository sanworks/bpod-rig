"""Module to hold a bunch of default values that are references in multiple places."""

import platformdirs

# Default Names
DEFAULT_DIR_NAME = "Bpod"
DEFAULT_SUBDIRS = ["Config", "Calibration", "Protocols", "Data", "Logs"]
DEFAULT_PROTOCOL_DIR_NAME = "Protocols"
DEFAULT_DATA_DIR_NAME = "Data"
DEFAULT_CONFIG_DIR_NAME = "Config"
DEFAULT_LOG_DIR_NAME = "Logs"
DEFAULT_BPODS_DIR_NAME = "Bpods"
DEFAULT_CALIBRATION_DIR_NAME = "Calibration"

# Defaults or unchanging paths
SYSTEM_CONFIG_DIR = platformdirs.user_config_path(DEFAULT_DIR_NAME, "sanworks")
SYSTEM_CONFIG_FILE = SYSTEM_CONFIG_DIR / "config.json"
DEFAULT_BPOD_PATH = platformdirs.user_documents_path() / DEFAULT_DIR_NAME

# Logging
TIME_FORMAT = "%Y-%m-%d-%H-%M-%S"
LOGFILE_PREFIX = "bpod"

if __name__ == "__main__":
    print(f"System config dir: {SYSTEM_CONFIG_DIR}")
    print(f"System config file: {SYSTEM_CONFIG_FILE}")
    print(f"Default Bpod path: {DEFAULT_BPOD_PATH}")
