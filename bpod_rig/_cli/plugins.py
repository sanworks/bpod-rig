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
                if _check_is_overlapping(app, entry.name):
                    logger.warning(
                        "Plugin %s is already registered. Skipping.",
                        entry.name,
                    )
                    continue

                # Attach the plugin as a subcommand group
                app.add_typer(plugin_app, name=entry.name)
            else:
                logger.warning(
                    "Plugin %s does not expose a Typer instance (was %s). Skipping.",
                    entry.name,
                    type(plugin_app).__name__,
                )
        except Exception:
            logger.warning("Failed to load plugin %s", entry.name, exc_info=True)


def _check_is_overlapping(app: typer.Typer, external_name: str) -> bool:
    """Check if the plugin app has overlapping commands with the main app."""
    main_commands = []
    for command in app.registered_commands:
        if command.name is None:
            if command.callback is not None:
                name = command.callback.__name__
            else:
                name = "unknown"
        else:
            name = command.name
        main_commands.append(name)
    main_commands = set(main_commands)
    plugin_commands = {
        command.name for command in app.registered_groups if command.name is not None
    }
    logger.debug(
        "Checking for overlapping of %s: main=%s, plugin=%s",
        external_name,
        main_commands,
        plugin_commands,
    )
    return external_name in main_commands or external_name in plugin_commands
