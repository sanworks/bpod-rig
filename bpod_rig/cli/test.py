"""Commands for testing bpod-rig and hardware."""

import sys
from pathlib import Path

import typer

import bpod_rig
import bpod_core

app = typer.Typer()

@app.command()
def software():
    """Test bpod_rig package installation and functionality."""
    try:
        import pytest
    except ImportError:
        typer.secho(
            "Error: pytest not installed. Install test dependencies with:",
            fg=typer.colors.RED,
        )
        typer.echo("  pip install bpod-rig[test]")
        typer.echo("  or uv pip install bpod-rig[test]")
        raise typer.Exit(1)
    
    # Find the tests directory in the installed package
    import bpod_rig
    package_path = Path(bpod_rig.__file__).parent.parent
    tests_path = package_path / "tests"
    
    if not tests_path.exists():
        typer.secho(
            "Error: Tests directory not found in installation.",
            fg=typer.colors.RED,
        )
        typer.echo(f"Expected location: {tests_path}")
        raise typer.Exit(1)
    
    typer.echo(f"Running tests from: {tests_path}")
    typer.echo(f"bpod_core version: {bpod_core.__version__}")
    typer.echo(f"bpod_rig version {bpod_rig.__version__}")
    typer.echo("")
    
    # Run pytest
    exit_code = pytest.main([str(tests_path), "-v"])
    
    if exit_code == 0:
        typer.secho("\n✓ All tests passed!", fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho("\n✗ Some tests failed.", fg=typer.colors.RED, bold=True)
    
    sys.exit(exit_code)

@app.command()
def hardware():
    """Test hardware devices."""
    typer.echo("Testing hardware connections for bpod-rig...")