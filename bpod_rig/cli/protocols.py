import typer

from bpod_rig.config import get_bpod_dir

app = typer.Typer()


@app.command()
def list():
    bpod_dir = get_bpod_dir()
    raise NotImplementedError("Protocol searcher required.")


if __name__ == "__main__":
    app()
