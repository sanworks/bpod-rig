from __future__ import annotations

import warnings

from datetime import datetime
from serial import SerialException

from bpod_core.bpod import Bpod, BpodError, RemoteBpod


from bpod_rig.log import BpodLogger
from bpod_rig.subject import BpodSubject
from bpod_rig.utils import get_func_params
from config.system_settings import SystemSettings

class SessionPaths:
    def __init__(self):
        pass


class SessionTimes:
    def __init__(self):
        # Times and Dates
        self.session_start_time: datetime | None = None
        self.session_end_time: datetime | None = None
        self.protocol_start_time: datetime | None = None
        self.protocol_end_time: datetime | None = None


class SessionParams:
    def __init__(self):
        # Session Information
        self.session_id: str | None = None
        self.subject: BpodSubject | None = None
        self.protocol: None = None
        self.system_info: dict | None = None

        self.times: SessionTimes | None = None
        self.paths: SessionPaths | None = None


class SessionManager:
    def __init__(self, *args, **kwargs):
        self.logger: BpodLogger | None = None
        self.system_settings: SystemSettings | None = None
        self.gui_handles: None = None

        self.bpod: Bpod | None = None
        self.params: SessionParams | None = None

    def start(self, warn: bool = True):
        self.logger.info("Starting Bpod Session!")
        if warn:
            warnings.warn(
                "BpodSession started outside of a context manager."
                " Make sure to call end() once finished to properly"
                " clean up the session!",
                stacklevel=2,
            )

        try:
            self._connect()
            self.logger.debug("Successfully connected to Bpod!")
        except SerialException as se:
            self.logger.error("Unable to open serial connection to Bpod!", exc_info=se)
        except BpodError as bpe:
            self.logger.error("Handshake with Bpod failed!", exc_info=bpe)

        self.times.session_start_time = datetime.now()

    def end(self):
        self.logger.info("Closing Bpod Session!")

        try:
            self._disconnect()
        except SerialException as se:
            self.logger.error("Unable to close serial connection to Bpod!", exc_info=se)

        self.times.session_end_time = datetime.now()

    def _connect(self):
        if self.bpod:
            self.logger.debug("Bpod already connected!")
            return

        connection_args = {}

        potential_args = get_func_params(Bpod.__init__, RemoteBpod.__init__)
        # Get the possible parameters for the Bpod/RemoteBpod constructors

        required_args = potential_args['required']
        for req_arg in required_args:
            if req_arg not in self._kwargs:
                raise AttributeError(
                    f"Required argument {req_arg} for Bpod is missing!"
                    )

        potential_args.pop('required')
        # Required args parsed, dropping the list

        for arg in potential_args:
            if arg in self._kwargs:
                self.logger.debug(
                    "Bpod connection argument %s found in BpodSession kwargs",
                    potential_args
                )
                connection_args[arg] = self._kwargs[arg]
        self.logger.debug("Attempting to connect to Bpod")
        self.bpod = Bpod(**connection_args)

    def _disconnect(self):
        if not self.bpod:
            raise ConnectionError("Bpod is already disconnected!")
        self.bpod.close()

    def __enter__(self):
        self.logger.debug("Enter context manager!")
        self.start(warn=False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.debug("Exiting context manager!")
        self.end()
        if exc_type is not None:
            self.logger.error("Error!", exc_info=(exc_type, exc_val, exc_tb))
