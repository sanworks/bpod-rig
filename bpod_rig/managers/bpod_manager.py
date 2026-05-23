import logging
import multiprocessing as mp
from multiprocessing.connection import Connection
from pathlib import Path
from typing import cast, Optional, TypeAlias

from bpod_core.bpod import Bpod, BpodInfo, discover_bpod, discover_remote_bpod

from bpod_rig.calibration.liquid.models import ValveDataManager
from bpod_rig.calibration.liquid.pending_calibration import PendingMeasurementsManager
from bpod_rig.log import BpodLogger
from bpod_rig.protocols.runner import load_protocol_function

SerialNumber: TypeAlias = str

class BpodManager:
    def __init__(self, *args, **kwargs) -> None:
        self.logger: BpodLogger = cast(BpodLogger, logging.getLogger(__name__))
        self._all_local_bpods: dict[SerialNumber, BpodInfo] | None = None
        # self.remote_bpods: dict[SerialNumber, BpodInfo] | None = None

        self.last_selected_bpod: BpodInfo | None = None


    def load(self):
        self._get_local_bpods()


    def select_bpod(self, serial: SerialNumber = None, index: int = 0) -> BpodInfo:
        """Returns a BpodInfo instance

        Function will return the BpodInfo instance with the given serial number or
        index. serial will always take precedence over index. If no parameter is
        provided, the first BpodInfo instance will be returned.

        Parameters
        ----------
        serial : SerialNumber (optional)
            SerialNumber of the Bpod to select
        index : int (optional)
            index of the Bpod to select

        Returns
        -------

        BpodInfo instance

        """

        if self._all_local_bpods is None:
            raise ValueError("No local Bpods found!")

        serials: list[SerialNumber] = list(self._all_local_bpods.keys())

        if serial is not None:
            if serial in self._all_local_bpods.keys():
                self.last_selected_bpod = self._all_local_bpods[serial]
            else:
                raise KeyError(f"Bpod {serial} not found!")

        if index > len(serials) or index < 0:
            raise IndexError(f"Index {index} out of range!")

        self.last_selected_bpod = self._all_local_bpods[serials[index]]
        return self.last_selected_bpod


    def _format_all_bpods_info(self):
        if self._all_local_bpods is None:
            return "No local Bpods found to list!"

        info = [
            f"[{i}]: Local Bpod\n"
            f"Name: {info.name} | Serial Number: {sn}\n"
            f"Port: {info.port} | Location: {info.location}\n\n"
            for i, sn, info in enumerate(self._all_local_bpods.items())
        ]

        return f"The following Bpods are available:\n{info}"


    def _get_local_bpods(self):
        local_bpods = discover_bpod()
        # remote_bpods = discover_remote_bpod()

        self._all_local_bpods = {
            info.serial_number: info
            for info in local_bpods
        }
        # self.remote_bpods = {
        #     info.serial_number: info
        #     for info in remote_bpods
        # }

        if self._all_local_bpods is None:
            self.logger.warning("No local Bpods found!")

        return self._all_local_bpods


    @property
    def bpod(self):
        if self.last_selected_bpod is not None:
            return self.last_selected_bpod
        else:
            return None

    def __str__(self):
        return self._format_all_bpods_info()


class BpodRigManager:
    port: str
    serial_number: str
    _connection: Bpod | None = None
    valve_manager: ValveDataManager
    folder: Path
    name: str
    process: Optional[mp.Process] = None
    parent_pipe: Optional[Connection] = None
    child_pipe: Optional[Connection] = None

    def __init__(self, folder: Path):
        self.folder = folder

    def run_protocol(self, protocol: Path) -> mp.Process:
        if self._connection is not None:
            self.disconnect()
        session_dir = self.folder / "sessions"
        # If polars are used ot exchange data
        # <https://docs.pola.rs/user-guide/misc/multiprocessing/#when-not-to-use-multiprocessing>
        ctx = mp.get_context("spawn")
        self.parent_pipe, self.child_pipe = ctx.Pipe()
        # This type checking is wack because the context returns SpawnProcess
        # Is it a subclass?
        self.process = ctx.Process(
            target=prepare_and_run_protocol_session, args=(protocol, session_dir)
        )  # type: ignore
        if self.process is None:
            raise RuntimeError("Failed to create process for protocol")
        self.process.start()
        return self.process

    def connect(self) -> None:
        if self._connection is not None:
            raise RuntimeError("Bpod connection already established")
        self._connection = Bpod(self.port)

    def disconnect(self) -> None:
        if self._connection is None:
            raise RuntimeError("Bpod connection not established")
        self._connection.close()
        self._connection = None

    def bpod(self) -> Bpod:
        if self._connection is None:
            raise RuntimeError("Bpod connection not established")
        return self._connection

    def get_valve_calibrator(self) -> PendingMeasurementsManager:
        return PendingMeasurementsManager(self.valve_manager)


class BpodMainManager:
    available_rigs: dict[SerialNumber, BpodRigManager]

    def __init__(self):
        self.available_rigs = {}

    def discover_rigs(self, rigs_folder: Path) -> None:
        for rig_folder in rigs_folder.iterdir():
            if rig_folder.is_dir():
                rig_manager = BpodRigManager(rig_folder)
                self.available_rigs[rig_manager.serial_number] = rig_manager

    def get_rig(
        self,
        *,
        serial_port: Optional[SerialNumber | str] = None,
        com: Optional[str] = None,
        name: Optional[str] = None,
    ) -> BpodRigManager:
        if (serial_port, com, name).count(None) != 2:
            raise ValueError("One of serial_port, com, or name should be provided")
        if len(self.available_rigs) == 0:
            raise RuntimeError("No rigs available")

        if serial_port is not None:
            key = serial_port
        elif com is not None:
            key = next(
                (
                    serial_number
                    for serial_number, rig_manager in self.available_rigs.items()
                    if rig_manager.port == com
                ),
                None,
            )
        elif name is not None:
            key = next(
                (
                    serial_number
                    for serial_number, rig_manager in self.available_rigs.items()
                    if rig_manager.name == name
                ),
                None,
            )
        else:
            raise AssertionError("Unreachable code")
        if key is None:
            raise ValueError("No rig found matching the provided identifier")
        return self.available_rigs[key]


def prepare_and_run_protocol_session(
    protocol_path: Path, session_dir: Path, protocol_args: list[str] | None = None
) -> None:
    """Run the protocol function.

    Parameters
    ----------
    protocol_path : Path
        Path to the protocol
    session_dir : Path
        Path to the existing session data folder
    """
    # either throw an error or set os.chdir to the protocol folder?
    if Path.cwd() != protocol_path.parent:
        raise RuntimeError(
            f"Current working directory {Path.cwd()} does not match protocol directory {protocol_path.parent}. "
            "Please run the protocol from its own directory or change to the protocol's directory before running."
        )

    protocol_function = load_protocol_function(protocol_path)
    pipe = mp.Pipe()
    import sys

    # prepare BpodSession
    # TODO: read session configs from session_dir if needed and pass to BpodSession
    # bpod_session = BpodSession(pipe[1], session_dir)

    original_args = None
    if protocol_args:
        original_args = sys.argv.copy()
        sys.argv = [sys.argv[0]] + protocol_args

    try:
        protocol_function(bpod_session)  # type: ignore
    finally:
        # This is unnecessary in a subprocess, but just in case
        if original_args:
            sys.argv = original_args
