from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer()


@app.command()
def run(
    protocol: Annotated[Path, typer.Argument(..., help="Path to the protocol file")],
    subject: Annotated[str, typer.Argument(..., help="Subject identifier")],
):
    raise NotImplementedError()


if __name__ == "__main__":
    app()
