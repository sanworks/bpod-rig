import logging
import warnings
from datetime import datetime
from pathlib import Path

from bpod_core.bpod import Bpod, BpodError, RemoteBpod
from serial import SerialException

from bpod_rig.config.system_settings import SystemSettings
from bpod_rig.protocols import BpodProtocol
from bpod_rig.utils import get_func_params

logger = logging.getLogger(__name__)


class BpodSession:
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

        self.bpod: Bpod | None = None
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
        self.protocol: BpodProtocol | None = None
        self.system_info: dict | None = None

        self.session_dir: Path | None = None

    def start(self, warn: bool = True):
        logger.info("Starting Bpod Session!")
        if warn:
            warnings.warn(
                "BpodSession started outside of a context manager."
                " Make sure to call end() once finished to properly"
                " clean up the session!",
                stacklevel=2,
            )

        try:
            self._connect()
        except SerialException as se:
            logger.error("Unable to open serial connection to Bpod!", exc_info=se)
        except BpodError as bpe:
            logger.error("Handshake with Bpod failed!", exc_info=bpe)

    def end(self):
        logger.info("Closing Bpod Session!")

        try:
            self._disconnect()
        except SerialException as se:
            logger.error("Unable to close serial connection to Bpod!", exc_info=se)

    def _connect(self):
        if self.bpod:
            logger.debug("Bpod already connected!")
            return

        connection_args = {}

        potential_args = get_func_params(Bpod.__init__, RemoteBpod.__init__)
        # Get the possible parameters for the Bpod/RemoteBpod constructors

        required_args = potential_args['required']
        for req_arg in required_args:
            if req_arg not in self._kwargs:
                raise AttributeError(f"Required argument {req_arg} for Bpod is missing!")

        potential_args.pop('required')
        # Required args parsed, dropping the list

        for arg in potential_args:
            if arg in self._kwargs:
                logger.debug(
                    "Bpod connection argument %s found in BpodSession kwargs", potential_args
                )
                connection_args[arg] = self._kwargs[arg]
        self.bpod = Bpod(**connection_args)

    def _disconnect(self):
        if not self.bpod:
            raise ConnectionError("Bpod is already disconnected!")
        self.bpod.close()

    def __enter__(self):
        self.start(warn=False)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()
