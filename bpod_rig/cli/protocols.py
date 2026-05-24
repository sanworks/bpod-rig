from typing import Annotated

import typer

from bpod_rig.config import get_settings

app = typer.Typer(help="Manage protocols", no_args_is_help=True,)


@app.command(name="list")
def list_protocols():
    """List all available protocols on the system."""
    _ = get_settings()
    raise NotImplementedError("Protocol searcher required.")

@app.command()
def open(
    protocol: Annotated[str | None, typer.Option()] = None,
    open_file: Annotated[bool, typer.Option()] = False,
    ):
    """Open a protoocl folder (or file)"""
    raise NotImplementedError("Protocol searcher required.")
    

if __name__ == "__main__":
    app()
