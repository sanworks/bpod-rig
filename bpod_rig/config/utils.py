import logging
from pathlib import Path

from bpod_rig.config.system_settings import BpodDir, SystemSettings
from bpod_rig.defaults import SYSTEM_CONFIG_DIR
from bpod_rig.IO import json_handler

logger = logging.getLogger(__name__)


def init_system_configuration(bpod_dir: Path) -> SystemSettings:
    system_paths = BpodDir(
        base_dir=bpod_dir,
    )

    system_settings = SystemSettings(paths=system_paths)
    return system_settings


def save_system_paths(
    system_paths: BpodDir, save_dir_override: Path | None
) -> None:
    """
    Save the system paths to the system configuration directory as json-formatted text

    Simultaneously will update the save_time field

    Parameters
    ----------
    system_paths : BpodDir
        SystemPaths instance to serialize and write to disk
    save_dir_override : Path | None
        Optional Path to override the default save directory. Default SYSTEM_CONFIG_DIR
        used if not provided

    Returns
    -------
    None
    """

    logger.debug("Saving system paths as JSON!")
    system_paths.update_modification_time()

    if save_dir_override is not None:
        save_dir = save_dir_override
    else:
        save_dir = SYSTEM_CONFIG_DIR

    system_paths_json = system_paths.model_dump_json(indent=2)
    json_handler.write_json(system_paths_json, save_dir, "paths")


