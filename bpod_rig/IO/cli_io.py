import logging
from pathlib import Path

import click

logger = logging.getLogger(__name__)

def yes_no_prompt(prompt: str) -> bool:
    try:
        return click.confirm(prompt, default=None)
    except click.Abort:
        logger.debug("User aborted before answering! Assuming answer is No/False")
        return False

def prompt_for_path(prompt: str) -> Path | None:
    try:
        return click.prompt(prompt,
                            type=click.Path(
                                exists=True,
                                file_okay=False,
                                dir_okay=True,
                                path_type=Path
                            )
                        )
    except click.Abort:
        logger.debug("User aborted before answering! Assuming user changed their mind")
        return None
