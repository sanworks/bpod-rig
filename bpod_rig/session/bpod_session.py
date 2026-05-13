import logging
from datetime import datetime
from inspect import signature
from pathlib import Path
from serial import SerialException

from bpod_core.bpod import Bpod, RemoteBpod, BpodError

from bpod_rig.config.system_settings import SystemSettings
from bpod_rig.protocols.bpod_protocol import BpodProtocol
from bpod_rig.utils import get_func_params

logger = logging.getLogger(__name__)

class BpodSession:
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

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
        self.protocol: BpodProtocol |  None = None
        self.system_info: dict | None = None

        self.session_dir: Path | None = None

    def connect(self):
        if self.bpod:
            raise ConnectionError("Bpod already connected!")
        else:
            connection_args = dict()

            args = get_func_params(Bpod.__init__, RemoteBpod.__init__)
            # Get the possible parameters for the Bpod/RemoteBpod constructors

            for arg in args:
                if arg in self._kwargs:
                    logger.debug("Bpod connection argument %s found in BpodSession kwargs", args)
                    connection_args[arg] = self._kwargs[arg]

            try:
                self.bpod = Bpod(**connection_args)
            except SerialException as se:
                logger.error("Unable to open serial connection to Bpod!", exc_info=se)
            except BpodError as bpe:
                logger.error("Handshake with Bpod failed!", exc_info=bpe)



    def start(self):
        pass

    def end(self):
        pass

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()
