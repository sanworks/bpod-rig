"""
Example machine/protocol management with subprocess module.

Provides utilities for running bpod protocols in isolated subprocess environments
with custom working directories.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Any, Optional, Protocol

import typer
from bpod_core.bpod import Bpod


def load_protocol_function(protocol_path: Path) -> ProtocolFunction:
    """Load the protocol function from the given protocol file.

    The protocol function is expected to have the same name as the file (without .py).
    For example, if the file is "my_protocol.py", it should define
    a function "my_protocol(bpod_session)".

    While it is functionally possible to have a protocol file free-floating in a folder,
    Bpod's protocol search expects protocols to be in a folder with the same name as the
    protocol function.

    Example:

        # protocols/my_protocol/my_protocol.py
        def my_protocol(bpod_session):
            bpod_session.connect()
            # do my protocol...

    """
    if not protocol_path.exists():
        raise FileNotFoundError(f"Protocol file not found: {protocol_path}")
    if not protocol_path.is_file():
        raise ValueError(f"Protocol path must be a file: {protocol_path}")

    spec = importlib.util.spec_from_file_location("protocol_module", protocol_path)
    if spec is None:
        raise ImportError(
            f"Could not create import spec for {protocol_path}. "
            f"This may be due to file permissions or an unsupported file type."
        )
    if spec.loader is None:
        raise ImportError(
            f"Import spec has no loader for {protocol_path}. "
            f"The file may not be importable by Python."
        )

    protocol_module = importlib.util.module_from_spec(spec)
    # Execute the module to define its contents
    spec.loader.exec_module(protocol_module)
    module_name = protocol_path.stem
    protocol_function: ProtocolFunction | None = getattr(
        protocol_module, module_name, None
    )

    if protocol_function is None:
        raise AttributeError(
            f"Protocol function '{module_name}' not found in {protocol_path}. "
            "Expected a function with the same name as the file (without .py)."
        )
    if not callable(protocol_function):
        raise TypeError(f"Protocol function in {protocol_path} is not callable")

    return protocol_function


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

    # prepare BpodSession
    # TODO: read session configs from session_dir if needed and pass to BpodSession
    bpod_session = BpodSession(session_dir)

    original_args = None
    if protocol_args:
        original_args = sys.argv.copy()
        sys.argv = [sys.argv[0]] + protocol_args

    try:
        protocol_function(bpod_session)
    finally:
        # This is unnecessary in a subprocess, but just in case
        if original_args:
            sys.argv = original_args


def run_protocol_async(
    protocol_path: Path,
    session_dir: Path,
    protocol_args: Optional[list[Any]] = None,
    python_executable: Optional[str | Path] = None,
) -> subprocess.Popen:
    """
    Run a bpod protocol asynchronously in a subprocess.

    This starts the protocol but doesn't wait for it to complete.
    Useful for long-running protocols that you want to monitor or control separately.

    Parameters
    ----------
        protocol_path
            Path to the protocol Python file to execute.
        protocol_args
            Positional arguments to pass to the protocol (optional)
        python_executable
            Path to Python executable (defaults to current interpreter)

    Returns
    -------
        Popen
            The subprocess handle for monitoring/control

    Raises
    ------
        FileNotFoundError
            If protocol_path doesn't exist
    """
    protocol_path = Path(protocol_path).resolve()

    # Validate that there's a protocol function to run
    _ = load_protocol_function(protocol_path)

    # Use current Python interpreter if not specified
    if python_executable is None:
        python_executable = sys.executable
    else:
        # unlikely but in case someone wants to run something quite custom
        python_executable = str(python_executable)

    cmd = [
        python_executable,
        "-m",
        "bpod_rig.protocols.environment",
        "run",
        str(protocol_path),
        str(session_dir),
    ]

    # Add arguments if provided
    if protocol_args:
        cmd.extend(str(arg) for arg in protocol_args)

    # Start subprocess
    process = subprocess.Popen(  # noqa: S603
        cmd,
        cwd=str(protocol_path.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return process


app = typer.Typer()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def run(
    ctx: typer.Context,
    protocol: Annotated[
        Path, typer.Argument(help="Path to the protocol Python file to execute.")
    ],
    session_dir: Annotated[
        Path, typer.Argument(help="Directory for Bpod session data.")
    ],
):
    prepare_and_run_protocol_session(protocol, session_dir, ctx.args)


@app.command()
def validate(
    protocol: Annotated[
        Path, typer.Argument(help="Path to the protocol Python file to validate.")
    ],
):
    """Validate that a protocol can be loaded and has a protocol function."""
    try:
        load_protocol_function(protocol)
        typer.echo(f"Protocol {protocol} is valid.")
    except Exception as e:
        typer.echo(f"Protocol {protocol} is invalid: {e}")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    app()
