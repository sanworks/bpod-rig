"""BpodSystem class to provide parameter access in a protocol"""

import logging
from pathlib import Path

from bpod_core.bpod import Bpod, RemoteBpod
from bpod_rig.config.system_settings import SystemSettings

class BpodSystem:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self._args = args
        self._kwargs = kwargs

        self.bpod: Bpod | None = None
        self.system_settings: SystemSettings | None = None
        self.session_params: dict | None = None
        self.gui_handles: None = None

        self.session_dir: Path | None = None
