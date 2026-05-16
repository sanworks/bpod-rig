"""Package providing configuration functionality for bpod-rig."""

from bpod_rig.config.system_settings import BpodDir
from bpod_rig.IO import startup


def get_bpod_dir() -> BpodDir:
    """Get the Bpod directory manager.

    Returns
    -------
    BpodDir
        The Bpod directory manager.

    """
    bpod_config_path = startup.get_bpod_dir_from_system()
    if bpod_config_path is None:
        raise FileNotFoundError(
            "Bpod directory path not found in system configuration file."
        )
    return BpodDir.model_validate_json(bpod_config_path.read_text())
