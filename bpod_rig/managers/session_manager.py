from __future__ import annotations

import multiprocessing as mp
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Optional, TypeAlias

from bpod_core.bpod import Bpod

from bpod_rig.calibration.liquid.models import ValveDataManager
from bpod_rig.calibration.liquid.pending_calibration import PendingMeasurementsManager
from bpod_rig.protocols.environment import load_protocol_function

SerialNumber: TypeAlias = str


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


class BpodSession:
    def __init__(self, pipe: Connection, session_dir: Path, connection_config=None):
        self._bpod = None
        self.session_dir = session_dir
        self._connection_config = connection_config
        self.pipe = pipe

    def connect(self):
        # use _connection_config to establish connection
        self._bpod = Bpod()  # TODO: this requires configuration

    @property
    def bpod(self) -> Bpod:
        if self._bpod is None:
            # or should this run the connect method?
            raise RuntimeError("Bpod session not connected. Call connect() first.")
        return self._bpod

    def run(self, sma):
        self.bpod.run(sma)


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
    bpod_session = BpodSession(pipe[1], session_dir)

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
