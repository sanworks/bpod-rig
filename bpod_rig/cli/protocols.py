import typer

app = typer.Typer()

@app.command()
def list():
    raise NotImplementedError("Protocol searcher required.")