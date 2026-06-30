"""
Bpod protocol session management.
"""
import atexit
import pdb
import signal
import sys
import traceback
from dataclasses import dataclass, field
from logging import getLogger
from multiprocessing import Process
from pathlib import Path
from typing import Any, Protocol

logger = getLogger(__name__)


class ClosableResource(Protocol):
    """Protocol for resources that can be cleaned up."""

    def close(self) -> None:
        """Close the resource."""
        ...


@dataclass
class SessionContext:
    session_folder: Path
    """Path to the session folder"""
    protocol_path: Path
    """Path to the protocol file"""
    ipc_handles: dict[str, Any]
    """Handles for communication between the main process and the protocol process"""
    debug: bool = False
    """Whether to run the protocol in debug mode"""
    _open_resources: list[ClosableResource] = field(default_factory=list, init=False)
    """List of open resources (COM ports, files, etc.) for cleanup"""

    def register_resource(self, resource: ClosableResource) -> None:
        """Register a resource (COM port, file, etc.) for automatic cleanup on exit."""
        self._open_resources.append(resource)

    def cleanup_resources(self) -> None:
        """Close all registered resources. Called automatically on protocol exit."""
        for resource in self._open_resources:
            try:
                if hasattr(resource, "close"):
                    resource.close()
                    logger.info("Closed resource: %s", resource)
            except Exception:  # noqa PERF203
                logger.exception("Error closing resource %s", resource)


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


# Public facing API for Bpod session management
@dataclass
class BpodSession:
    """Bpod session object providing access to hardware and session data."""
    session_folder: Path


def get_session(session_folder_override: Path | None = None) -> BpodSession:
    """
    Returns the current Bpod session.

    Parameters
    ----------
    session_folder_override : Path, optional
        If provided, overrides the default session folder path generated during protocol selection.

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
    bpod_system = BpodSession(session_folder=context.session_folder)
    return bpod_system


# Magic that starts a new process for the protocol and sets up IPC handles


def start_protocol_process(
    session_folder: Path,
    protocol_path: Path,
    ipc_handles: dict[str, Any],  # IPC Event, Queue, etc.
    *,
    debug: bool = False,
) -> None:
    context = SessionContext(
        session_folder=session_folder,
        protocol_path=protocol_path,
        ipc_handles=ipc_handles,
        debug=debug,
    )
    proc = Process(
        target=run_protocol,
        args=(context,),
    )
    proc.start()


def run_protocol(session: SessionContext) -> None:
    """
    Runs a protocol in the given session folder with automatic resource cleanup.

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
    def signal_handler(signum: int, _) -> None:  # noqa: ANN001
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
    namespace = {
        "__name__": "__main__",
        "__file__": str(session.protocol_path),
    }

    try:
        code = compile(
            session.protocol_path.read_text(), str(session.protocol_path), "exec"
        )

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
