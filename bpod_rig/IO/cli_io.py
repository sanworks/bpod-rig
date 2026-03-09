import logging
from pathlib import Path

import click

logger = logging.getLogger(__name__)
@click.command()
@click.argument('prompt')
def yes_no_prompt(prompt: str) -> bool | None:
    logger.debug("Asking user to respond [y/n] to the following prompt: %s", prompt)
    try:
        return click.confirm(prompt, default=None)
    except click.Abort:
        logger.debug("User aborted before answering!")
        return None

@click.command()
@click.argument('prompt')
def prompt_for_path(prompt: str) -> Path | None:
    logger.debug("Asking user to select a path: %s", prompt)
    try:
        return click.prompt(prompt,
                            type=click.Path(
                                exists=True,
                                file_okay=False,
                                dir_okay=True,
                                path_type=Path
                            ),
                            default=None
                        )
    except click.Abort:
        logger.debug("User aborted before answering!")
        return None
