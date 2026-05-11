from datetime import datetime
from pathlib import Path

from bpod_core.bpod import Bpod, RemoteBpod

from bpod_rig.config.system_settings import SystemSettings


class BpodSession:
    def __init__(self, *args, **kwargs):
        self.bpod: Bpod | RemoteBpod | None = None
        self.system_settings: SystemSettings | None = None
        self.session_params: dict | None = None
        self.gui_handles: None = None

        # Times and Dates
        self.session_start_time: datetime | None = None
        self.session_end_time: datetime | None = None
        self.protocol_start_time: datetime | None = None
        self.protocol_end_time: datetime | None = None

        # Session Information
        self.session_id: str | None = None
        self.subject: None = None
        self.protocol: None = None
        self.system_info: dict | None = None

        self.session_dir: Path | None = None

    def start(self):
        pass

    def end(self):
        pass

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()
