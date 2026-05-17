"""Package providing configuration functionality for bpod-rig."""

from bpod_rig.config.system_settings import SystemSettings, load_system_configuration

from bpod_rig.defaults import SYSTEM_CONFIG_FILE

def get_bpod_dir() -> SystemSettings:
    """Get system settings.

    Returns
    -------
    SystemSettings
        The Bpod directory manager.
    """
    # TODO: handle file system loading properly
    return load_system_configuration(SYSTEM_CONFIG_FILE)
