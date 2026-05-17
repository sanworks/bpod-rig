"""Commands for testing bpod-rig and hardware."""

import os
import sys
from pathlib import Path

import bpod_core
import typer

import bpod_rig

app = typer.Typer()


def prepare_tests() -> Path:
    try:
        import pytest  # noqa: F401
    except ImportError:
        typer.secho(
            "Error: pytest not installed. Install test dependencies with:",
            fg=typer.colors.RED,
        )
        typer.echo("  pip install bpod-rig[test]")
        typer.echo("  or uv pip install bpod-rig[test]")
        raise typer.Exit(1) from None

    # Find the tests directory in the installed package
    package_path = Path(bpod_rig.__file__).parent.parent
    tests_path = package_path / "tests"

    if not tests_path.exists():
        typer.secho(
            "Error: Tests directory not found in installation.",
            fg=typer.colors.RED,
        )
        typer.echo(f"Expected location: {tests_path}")
        raise typer.Exit(1)

    typer.echo(f"Tests found: {tests_path}")
    typer.echo(f"bpod_core version: {bpod_core.__version__}")
    typer.echo(f"bpod_rig version {bpod_rig.__version__}")
    typer.echo("")

    return tests_path


@app.command()
def software():
    """Test bpod_rig package installation and functionality."""
    tests_path = prepare_tests()

    # Run pytest
    exit_code = os.system(f"pytest {tests_path} -v")  # noqa: S605

    if exit_code == 0:
        typer.secho("\n✓ All tests passed!", fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho("\n✗ Some tests failed.", fg=typer.colors.RED, bold=True)

    sys.exit(exit_code)


@app.command()
def hardware():
    """Test hardware devices."""
    typer.echo("Testing hardware connections for bpod-rig...")
    raise NotImplementedError("Hardware tests not implemented yet.")
