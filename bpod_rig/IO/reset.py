# Module to delete all Bpod directories
import shutil
from pathlib import Path
from typing import Iterable

from bpod_rig.IO import cli_io


def reset_all(directories: Iterable[Path], force=False) -> bool:
    """Function to hard reset all Bpod directories on this machine.

    USE AT OWN RISK!
    THIS WILL DELETE ALL OF YOUR BPOD-RELATED DATA IN AN IRREVERSIBLE MANNER
    During development the need to delete and recreate the Bpod directories is a common
    occurrence. This function will delete all the Bpod-related directories--resetting
    this machine to a clean state

    Parameters
    ----------
    directories : Iterable[Path]
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
        confirmation = cli_io.yes_no_prompt("Are you sure you want to delete ALL Bpod-"
                                          "related directories on this machine?")
        if confirmation:
            confirmation &= cli_io.yes_no_prompt("Final warning: Are you SURE you want to delete all Bpod-related directories?")

        if not confirmation:
            return False

    for directory in directories:
        shutil.rmtree(str(directory))

    return True
