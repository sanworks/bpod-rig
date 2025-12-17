import logging
from pathlib import Path

import click

logger = logging.getLogger(__name__)

def yes_no_prompt(prompt: str) -> bool:
    response = ''

    while response not in ['y', 'n', 'Y', 'N']:
        response = click.prompt(prompt, prompt_suffix=' [y/N] ')

    if response in ['y', 'Y']:
        return True
    else:
        return False

def prompt_for_path(prompt: str) -> Path:
    validated = False
    path = []

    while not validated:
        unverified_path = click.prompt(prompt)
        response = yes_no_prompt(f"Is {unverified_path} the correct path?")
        if response:
            try:
                path = Path(unverified_path)
                validated = True
            except Exception as e:
                logger.error("Invalid path: %s", exc_info=e)
                click.echo("Invalid path entered, please try again.", err=True)

    return path

