from pathlib import Path

from bpod_rig import log
from bpod_rig.config.system_settings import BpodDir, SystemSettings

logger = log.get_logger(__name__)


def init_system_configuration(bpod_dir: Path) -> SystemSettings:
    system_paths = BpodDir.create(
        base_dir=bpod_dir,
    )

    system_settings = SystemSettings.create(paths=system_paths)
    return system_settings
