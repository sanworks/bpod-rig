# Module to delete all Bpod directories
import shutil
from collections.abc import Iterable
from pathlib import Path

from bpod_rig import log
from bpod_rig.cli import prompts

logger = log.get_logger(__name__)


def reset_all(directories: Iterable[Path | str], *, force: bool = False) -> bool:
    """Function to hard reset all Bpod directories on this machine.

    USE AT OWN RISK!
    THIS WILL DELETE ALL OF YOUR BPOD-RELATED DATA IN AN IRREVERSIBLE MANNER
    During development the need to delete and recreate the Bpod directories is a common
    occurrence. This function will delete all the Bpod-related directories--resetting
    this machine to a clean state

    Parameters
    ----------
    directories : Iterable[Path | str]
        Iterable of Bpod-related directories to delete
    force : bool, optional
        User will be prompted to confirm if set to false
        If set to true, everything will be deleted without prompting

    Returns
    -------
        bool
            False if aborted
            True if directories were deleted
    """
    if not force:
        confirmation = prompts.yes_no_prompt(
            "Are you sure you want to delete ALL Bpod-"
            "related directories on this machine?"
        )
        if confirmation:
            final_confirmation = prompts.yes_no_prompt(
                "Final warning: Are you SURE you want to delete all "
                "Bpod-related directories?"
            )
            if not final_confirmation:
                return False
        else:
            return False

    for directory in directories:
        if not isinstance(directory, Path):
            directory = Path(directory)  # noqa: PLW2901
        if directory.exists() and "bpod" in directory.name.lower():
            # A small sanity check so this does not just start deleting stuff
            logger.debug("Deleting: %s", directory)
            shutil.rmtree(str(directory))

    return True
