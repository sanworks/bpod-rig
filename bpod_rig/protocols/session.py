"""
Bpod protocol session management.

This module manages the running of a protocol within a protocol session.


"""

from __future__ import annotations

import atexit
import multiprocessing as mp
import pdb
import signal
import sys
import traceback
from dataclasses import dataclass, field
from logging import getLogger
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from collections.abc import Callable
    from multiprocessing.synchronize import Event as mp_Event_type
    from pathlib import Path
    from types import FrameType

logger = getLogger(__name__)

MULTIPROCESSING_START_METHOD = "spawn"
# spawn is a bit slower but more robust
mp.set_start_method(MULTIPROCESSING_START_METHOD, force=True)


class IPCHandles(TypedDict):
    errors: mp.Queue
    user_log: mp.Queue
    protocol_run_state: mp_Event_type
    """When set, protocol should run. When cleared, protocol should pause."""


def create_ipc_handles() -> IPCHandles:
    return IPCHandles(
        errors=mp.Queue(),
        user_log=mp.Queue(),
        protocol_run_state=mp.Event(),
    )


@dataclass
class SessionContext:
    """A context object that holds information unavailble through the session folder.

    Passed to the protocol process to enable building of the BpodSession object.
    """

    session_folder: Path
    """Path to the session folder"""
    protocol_path: Path
    """Path to the protocol file"""
    ipc_handles: IPCHandles
    """Handles for communication between the main process and the protocol process"""
    debug: bool = False
    """Whether to run the protocol in debug mode"""
    _open_resources: list[Callable] = field(default_factory=list, init=False)
    """List of open resources (COM ports, files, etc.) for cleanup"""
    _cleaned_up: bool = field(default=False, init=False)
    """Whether resources have already been cleaned up."""

    @property
    def config_folder(self) -> Path:
        """Path to the config folder within the session folder."""
        path = self.session_folder / "config"
        path.mkdir(exist_ok=True)
        # TODO: make this not jank
        return path

    def register_resource(self, resource: Callable) -> None:
        """Register a resource (COM port, file, etc.) for automatic cleanup on exit."""
        self._open_resources.append(resource)

    def cleanup_resources(self) -> None:
        """Close all registered resources. Called automatically on protocol exit."""
        if self._cleaned_up:
            return

        self._cleaned_up = True
        for resource in self._open_resources:
            try:
                logger.info("Closing resource: %s", resource.__class__)
                resource()
            except Exception:  # noqa PERF203
                logger.exception("Error closing resource %s", resource)
        self._open_resources.clear()


_CONTEXT: SessionContext | None = None


def get_active_session_context() -> SessionContext:
    """Returns the active session context."""
    global _CONTEXT
    if _CONTEXT is None:
        raise RuntimeError("No active session context found.")
    return _CONTEXT


def _reset_context() -> None:
    """Resets the active session context."""
    global _CONTEXT
    _CONTEXT = None


# USER API
class BpodSession:
    """Bpod session object providing access to hardware and session data."""

    session_folder: Path
    """Path to the session folder where data is being saved."""
    protocol_path: Path
    """Path to original protocol file."""
    _ipc_handles: IPCHandles

    def handle_pause_condition(self) -> None:
        """Waits if the protocol manager has paused the protocol."""
        event = self._ipc_handles.get("protocol_run_state")
        if event is not None:
            logger.info("Waiting for protocol run state to be cleared...")
            event.wait()
            logger.info("Protocol run state cleared.")

    def log_user_message(self, message: str) -> None:
        """Logs a user message to the protocol manager."""
        self._ipc_handles["user_log"].put(message)

    @classmethod
    def from_context(cls, context: SessionContext) -> BpodSession:
        """Creates a BpodSession from a SessionContext."""
        session = cls()
        session.session_folder = context.session_folder
        session.protocol_path = context.protocol_path
        session._ipc_handles = context.ipc_handles
        return session


@dataclass
class GetSessionOverrides:
    """Overrides for get_session function."""

    session_folder_override: Path | None = None
    """The default session folder path generated during protocol selection."""


# USER API
def get_session(overrides: GetSessionOverrides | None = None) -> BpodSession:
    """
    Returns the current Bpod session for the protocol.

    Parameters
    ----------
    overrides : GetSessionOverrides, optional
        Object containing overrides for the session run..

    Returns
    -------
        BpodSession: The current Bpod session.
    """
    """
    This is the user-facing API for accessing the Bpod session.
    It retrieves the context and builds the BpodSession object that provides access
    to hardware and session data.
    """
    context = get_active_session_context()
    bpod_system = BpodSession.from_context(context)
    if overrides:
        raise NotImplementedError("Overrides are not yet implemented.")
    return bpod_system


# Magic that starts a new process for the protocol and sets up IPC handles


def start_protocol_process(
    session_folder: Path,
    protocol_path: Path,
    ipc_handles: IPCHandles,  # IPC Event, Queue, etc.
    *,
    debug: bool = False,
) -> mp.Process:
    """Runs a protocol in a separate process.

    This function is called by the GUI/CLI to start a protocol.
    """
    context = SessionContext(
        session_folder=session_folder,
        protocol_path=protocol_path,
        ipc_handles=ipc_handles,
        debug=debug,
    )
    proc = mp.Process(
        target=run_protocol,
        args=(context,),
    )
    proc.start()
    return proc


def run_protocol(session: SessionContext) -> None:
    """
    Runs a protocol in the given session folder with automatic resource cleanup.

    This function should be run inside a subprocess.

    This function uses multiple layers of cleanup to ensure COM ports and other
    resources are closed even if the protocol crashes:
    - Layer 1: atexit handler (abnormal process exits)
    - Layer 2: Signal handlers (SIGTERM, SIGINT/Ctrl+C)
    - Layer 3: finally block (normal exit or exceptions)

    Args:
        session (SessionContext): The session context.
    """
    # Set the global context for the protocol process
    # This allows get_session to work within the protocol process
    debug = session.debug

    # ==================================================
    # Prepare the environment for the protocol execution
    # ==================================================

    # Make context available to the protocol code
    global _CONTEXT
    _CONTEXT = session  # Set the global context for the protocol process

    # Register cleanup on process exit (catches abnormal exits)
    atexit.register(session.cleanup_resources)

    # Handle kill signals (SIGTERM, SIGINT/Ctrl+C)
    def signal_handler(signum: int, _: FrameType | None) -> None:
        logger.info("Caught signal %d, cleaning up resources...", signum)
        session.cleanup_resources()
        sys.exit(1)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Add the directory of the protocol to sys.path so imports
    # within the protocol can work correctly
    protocol_dir = session.protocol_path.parent
    if str(protocol_dir) not in sys.path:
        sys.path.insert(0, str(protocol_dir))

    # Define namespace of the protocol so that it can access
    # the session context and other variables
    # Sort of a trick to make the protocol code think it's running as __main__ while
    # still having access to the session context and being cleaned up.
    namespace = {
        "__name__": "__main__",
        "__file__": str(session.protocol_path),
    }

    try:
        code_text = session.protocol_path.read_text()
        code = compile(code_text, str(session.protocol_path), "exec")
        session.config_folder.joinpath(session.protocol_path.name).write_text(code_text)

        # Execute the protocol code in the context of the session
        # Given that we're already executing a user define protocol,
        # the trust/security is the same as if we were importing the protocol
        # as a module i.e. exec is acceptable here.
        exec(  # noqa: S102
            code,
            namespace,
        )
    except Exception as e:
        if debug:
            pdb.post_mortem()
        tb = traceback.format_exc()
        error_info = {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": tb,
            "line_number": e.__traceback__.tb_lineno if e.__traceback__ else None,
        }
        logger.exception("Error info: %s", error_info)

        # Send error via IPC if available
        if "errors" in session.ipc_handles:
            try:
                session.ipc_handles["errors"].put(error_info)
            except Exception:
                logger.exception("Failed to send error info via IPC.")

        raise
    finally:
        # Always cleanup (normal exit or exception)
        logger.info("Protocol finished, cleaning up resources...")
        session.cleanup_resources()
        _reset_context()
