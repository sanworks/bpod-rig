"""Module to hold a bunch of default values that are references in multiple places."""
import sys
from pathlib import Path

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
_SYSTEM_PYTHON = Path(sys.base_prefix)
_BPOD_RIG_PYTHON = Path(sys.prefix)
SYSTEM_DIR = _BPOD_RIG_PYTHON.parent
SYSTEM_CONFIG_FILE = SYSTEM_DIR / "config.json"
DEFAULT_BPOD_PATH = platformdirs.user_documents_path() / DEFAULT_DIR_NAME

# Logging
TIME_FORMAT = "%Y-%m-%d-%H-%M-%S"
LOGFILE_PREFIX = "bpod"

if __name__ == "__main__":
    print(f"System python path: {_SYSTEM_PYTHON}")
    print(f"Bpod Rig python path: {_BPOD_RIG_PYTHON}")
    print(f"System dir: {SYSTEM_DIR}")
    print(f"System config file: {SYSTEM_CONFIG_FILE}")
    print(f"Default Bpod path: {DEFAULT_BPOD_PATH}")
