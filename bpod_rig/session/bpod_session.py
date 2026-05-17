from __future__ import annotations
import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from bpod_core.bpod import Bpod, BpodError, RemoteBpod
from serial import SerialException

from bpod_rig.config.system_settings import SystemSettings
from bpod_rig.utils import get_func_params

if TYPE_CHECKING:
    from bpod_rig.protocols import BpodProtocol

class BpodSession:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
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


    def set_protocol(self, protocol: BpodProtocol | Callable):
        from bpod_rig.protocols import BpodProtocol
        # import this here to avoid circular dependencies
        if isinstance(protocol, type) and issubclass(protocol, BpodProtocol):
            self.logger.debug("Setting protocol to BpodProtocol object!")
            self.protocol = protocol
        elif isinstance(protocol, Callable):
            self.logger.debug("Setting protocol to Callable object!")
            bpod_protocol = BpodProtocol(self, protocol_function=protocol)
            self.protocol = bpod_protocol
        else:
            raise TypeError("Invalid protocol object or function passed!")



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

        self.session_start_time = datetime.now()


    def end(self):
        self.logger.info("Closing Bpod Session!")

        try:
            self._disconnect()
        except SerialException as se:
            self.logger.error("Unable to close serial connection to Bpod!", exc_info=se)

        self.session_end_time = datetime.now()


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
                raise AttributeError(f"Required argument {req_arg} for Bpod is missing!")

        potential_args.pop('required')
        # Required args parsed, dropping the list

        for arg in potential_args:
            if arg in self._kwargs:
                self.logger.debug(
                    "Bpod connection argument %s found in BpodSession kwargs", potential_args
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
