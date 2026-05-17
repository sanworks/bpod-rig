"""Helpers for running tests from CLI."""

import os
from pathlib import Path

import bpod_core
import typer

import bpod_rig


def prepare_tests() -> Path:
    """Find the tests directory in the installed package."""
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
    typer.echo(f"bpod_rig version: {bpod_rig.__version__}")
    typer.echo("")

    return tests_path


def report_test_result(exit_code: int):
    """Print end-result message to console."""
    if exit_code == 0:
        typer.secho("\n✓ All tests passed!", fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho("\n✗ Some tests failed.", fg=typer.colors.RED, bold=True)


def run_test(test_path: Path, hardware: bool = False) -> int:
    """Execute pytest on test path."""
    run_command = f"pytest {test_path} -v"
    if hardware:
        raise NotImplementedError("Hardware tests not implemented yet.")
    # pytest.main doesn't work because of log capture issues
    # refactoring all cli to typer may allow us to use pytest.main in the future
    exit_code = os.system(run_command)  # noqa: S605
    return exit_code
