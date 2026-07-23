"""Protocol running cli command.

This file should only define the command run, to ensure that bpod run is
only the single command.
"""

import logging
from typing import Annotated

import typer
from rich import print  # noqa: A004

from bpod_rig.config import get_settings
from bpod_rig.protocols import manager, session

logger = logging.getLogger(__name__)

app = typer.Typer()


@app.command()
def run(
    protocol: Annotated[
        str,
        typer.Argument(
            ..., help="Name of the protocol file, or path to the protocol file"
        ),
    ],
    subject: Annotated[str, typer.Argument(..., help="Subject identifier")],
    port: Annotated[str | None, typer.Option(..., help="COM port for the Bpod")] = None,  # noqa
    serial_number: Annotated[  # noqa
        int | None, typer.Option(..., help="Serial number of the Bpod")
    ] = None,
    protocol_args: Annotated[  # noqa
        str | None,
        typer.Option(..., help="Additional arguments for the protocol"),
    ] = None,
) -> None:
    """Run a protocol on the Bpod Rig.

    A protocol can be specified by its name if in protocol folder, or by a path to the
    protocol file.
    """
    system_settings = get_settings()
    protocol_manager = manager.ProtocolManager(system_settings.paths.protocol_dir)
    protocol_path = protocol_manager.find_protocol_file(protocol)
    protocol_name = protocol_path.stem
    print(f"Running protocol: [bold]{protocol_name}[/bold]")
    print(f"Found protocol file: {protocol_path}")

    data_dir = system_settings.paths.data_dir
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")
    # check if subject is "registered"
    subject_dir = data_dir / subject
    if not subject_dir.exists():
        raise FileNotFoundError(
            f"Subject directory does not exist: {subject_dir}. "
            "Please register the subject first."
        )  # TODO: this requires manually creating the subject folder in the data folder
    session_folder = session.create_session_folder(data_dir, subject, protocol_name)
    print(f"Session folder created: {session_folder}")

    print("Starting session...")
    session_context = session.start_session(session_folder, protocol_path)
    session_context.process.join()
    print(f"Protocol process exited with code: {session_context.process.exitcode}")
