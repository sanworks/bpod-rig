import importlib.metadata

import typer


def load_plugins(app: typer.Typer) -> None:
    """Discover third-party packages registered under the unique group key."""
    entries = importlib.metadata.entry_points(group="bpod.cli_plugins")

    for entry in entries:
        try:
            # Dynamically load the plugin module
            plugin_app = entry.load()

            # Ensure the plugin exposes a Typer instance
            if isinstance(plugin_app, typer.Typer):
                # Attach the plugin as a subcommand group
                app.add_typer(plugin_app, name=entry.name)
        except Exception as e:  # noqa: PERF203
            print(f"Failed to load plugin {entry.name}: {e}")
