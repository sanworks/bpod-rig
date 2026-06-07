"""BpodSystem class to provide parameter access in a protocol."""

import logging
from datetime import datetime
from pathlib import Path

from bpod_core.bpod import Bpod

from bpod_rig.config.system_settings import SystemSettings
from bpod_rig.subject import BpodSubject


class BpodTimes:
    def __init__(self):
        self.session_start_time: datetime = datetime.now()
        self.session_end_time: datetime | None = None
        self.protocol_start_time: datetime | None = None
        self.protocol_end_time: datetime | None = None


class BpodSystem:
    def __init__(
        self,
        bpod: Bpod,
        system_settings: SystemSettings,
        subject: BpodSubject,
        protocol: None,
    ):
        self.logger = logging.getLogger(__name__)

        self.bpod: Bpod = bpod
        self.system_settings: SystemSettings = system_settings
        self.protocol: None = protocol
        self.subject: BpodSubject = subject

        self.times: BpodTimes = BpodTimes()

        self.gui_handles: None = None
        self.session_id: str | None = None

        self._generate_session_id()


    def _generate_session_id(self):
        if self.subject.id is None:
            raise ValueError("Subject must have an ID to initialize BpodSystem!")

        self.session_id = f"{self.subject.id}_{str(self.times.session_start_time)}"


def new_bpod_system(bpod: Bpod,
        system_settings: SystemSettings,
        subject: BpodSubject,
        protocol: None):

    bps = BpodSystem(bpod, system_settings, subject, protocol)

    return bps
