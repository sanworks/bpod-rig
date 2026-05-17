import typer

from bpod_rig.config import get_settings

app = typer.Typer()


@app.command()
def list():  # noqa: A001
    _ = get_settings()
    raise NotImplementedError("Protocol searcher required.")


if __name__ == "__main__":
    app()
