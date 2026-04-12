"""Module to hold a bunch of default values that are references in multiple places."""

import platformdirs

# Default Names
DEFAULT_DIR_NAME = "Bpod"
DEFAULT_SUBDIRS = ["Config", "Calibration", "Protocols", "Data", "Logs"]
DEFAULT_PROTOCOL_DIR_NAME = "Protocols"
DEFAULT_DATA_DIR_NAME = "Data"
DEFAULT_CONFIG_DIR_NAME = "Config"
DEFAULT_LOG_DIR_NAME = "Logs"

# Defaults or unchanging paths
SYSTEM_CONFIG_DIR = platformdirs.user_config_path(DEFAULT_DIR_NAME, "sanworks")
SYSTEM_CONFIG_FILE = SYSTEM_CONFIG_DIR / "config.json"
DEFAULT_BPOD_PATH = platformdirs.user_documents_path() / DEFAULT_DIR_NAME
