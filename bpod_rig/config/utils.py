import logging
from pathlib import Path

from bpod_rig.config.system_settings import BpodDir, SystemSettings

logger = logging.getLogger(__name__)

def init_system_configuration(bpod_dir: Path) -> SystemSettings:
    system_paths = BpodDir(
        base_dir=bpod_dir,
    )

    system_settings = SystemSettings(paths=system_paths)
    return system_settings
