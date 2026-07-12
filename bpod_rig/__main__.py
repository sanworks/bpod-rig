"""main entry point for bpod-rig."""

import logging
from logging.config import dictConfig
from typing import Annotated, cast

import typer
from rich import print  # noqa: A004

from bpod_rig.cli.protocols import app as protocols_app
from bpod_rig.cli.run import app as run_app
from bpod_rig.cli.test import app as test_app
from bpod_rig.config import startup
from bpod_rig.config.startup import CLIStartupChoiceAdapter, initialize_bpod_system
from bpod_rig.defaults import DEFAULT_BPOD_PATH
from bpod_rig.log import BpodLogger, get_log_config

DEBUG = True

# Set up logging here
logging_config = get_log_config(debug=DEBUG)
dictConfig(logging_config)
logging.setLoggerClass(BpodLogger)
logger: BpodLogger = cast("BpodLogger", logging.getLogger(__name__))

app = typer.Typer(no_args_is_help=True)
app.add_typer(protocols_app, name="protocols")
app.add_typer(test_app, name="test")
app.add_typer(run_app)  # is a single command


@app.command()
def init() -> None:

    result = initialize_bpod_system(
        choices=CLIStartupChoiceAdapter(),
        default_bpod_path=DEFAULT_BPOD_PATH,
        logger=logger,
    )
    if result.state not in (startup.InitState.COMPLETED, startup.InitState.SKIPPED):
        logger.error(
            "Initialization failed: %s",
            result,
        )
        print(f"[red]✖ Initialization failed: {result.message}[/red]")
        raise typer.Exit(code=-1)

    print(f"[green]✔ {result.message}[/green]")
    print(f"  [dim]Bpod directory is: {result.bpod_path}[/dim]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
