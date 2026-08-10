import importlib.metadata

import typer

from bpod_rig.log import get_logger

logger = get_logger(__name__)

TYPER_PLUGIN_GROUP = "bpod.cli_plugins"


def load_plugins(app: typer.Typer) -> None:
    """Discover and add third-party packages registered under the group key."""
    entries = importlib.metadata.entry_points(group=TYPER_PLUGIN_GROUP)
    logger.debug("Discovered %d plugins for %s.", len(entries), TYPER_PLUGIN_GROUP)
    if not entries:
        return
    for entry in entries:
        try:
            # Dynamically load the plugin module
            plugin_app = entry.load()

            # Ensure the plugin exposes a Typer instance
            if isinstance(plugin_app, typer.Typer):
                # Attach the plugin as a subcommand group
                app.add_typer(plugin_app, name=entry.name)
            else:
                logger.warning(
                    "Plugin %s does not expose a Typer instance. Skipping.",
                    entry.name,
                )
        except Exception:  # noqa: PERF203
            logger.warning("Failed to load plugin %s", entry.name, exc_info=True)
