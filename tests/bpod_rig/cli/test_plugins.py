"""CLI supports third party entry point plugins."""

from unittest.mock import MagicMock, patch

import pytest
import typer

from bpod_rig.__main__ import app, load_plugins


@pytest.fixture(autouse=True)
def reset_app_state():
    """Fixtures to reset the Typer app state before each test."""
    # Clear registered subcommands from the Typer app
    app.registered_groups = []
    yield


def test_load_plugins_success():
    """Test that a valid Typer plugin is successfully added as a subcommand."""
    mock_plugin_app = typer.Typer()

    # Patch entry_points and load plugin
    mock_entry = MagicMock()
    mock_entry.name = "my-plugin"
    mock_entry.load.return_value = mock_plugin_app
    with patch("importlib.metadata.entry_points") as mock_entry_points:
        mock_entry_points.return_value = [mock_entry]

        load_plugins(app)

    mock_entry_points.assert_called_once_with(group="bpod.cli_plugins")
    mock_entry.load.assert_called_once()

    assert len(app.registered_groups) == 1
    assert app.registered_groups[0].name == "my-plugin"


def test_load_plugins_failure():
    """Test that an exception during plugin load is caught and logged."""
    mock_entry = MagicMock()
    mock_entry.name = "broken-plugin"
    mock_entry.load.side_effect = Exception("Import error")

    # entry_points
    with patch("importlib.metadata.entry_points") as mock_entry_points:
        mock_entry_points.return_value = [mock_entry]

        load_plugins(app)

    assert len(app.registered_groups) == 0, "No plugins should be registered on failure"


def test_load_plugins_no_plugins():
    """Test that no plugins are loaded when entry_points returns an empty list."""
    with patch("importlib.metadata.entry_points") as mock_entry_points:
        mock_entry_points.return_value = []

        load_plugins(app)

    assert len(app.registered_groups) == 0, (
        "No plugins should be registered when none are found"
    )
