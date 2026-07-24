from pathlib import Path
from typing import Annotated

# import click
import typer

from bpod_rig import log

logger = log.get_logger(__name__)

app = typer.Typer()


def yes_no_prompt(prompt: str) -> bool | None:
    logger.debug("Asking user to respond [y/n] to the following prompt: %s", prompt)
    try:
        return typer.confirm(prompt, default=None)
    except typer.Abort:
        logger.debug("User aborted before answering!")
        return None


@app.command()
def yes_no_prompt_cli_runner(
    prompt: Annotated[str, typer.Option()],
) -> bool | None:
    return yes_no_prompt(prompt)


def verify_path(
    unverified_path: str, *, prompt_for_file: bool = False, must_exist: bool = True
) -> Path:
    """Verify that the user provides a valid path.

    Typer does not have type checking for non-app usage of its commands. This function
    verifies that a path is for the expected type (file or directory) and that
    it exists.


    Parameters
    ----------
    unverified_path : str
        Unverified path provided by user. Is type-cast into a pathlib.Path
    prompt_for_file : bool (optional)
        By default, verify_path will ensure unverified_path points to a directory. If
        the user should be providing a file, prompt_for_file should be set to True
    must_exist : bool (optional)
        By default, verify_path will ensure the path provided by the user exists. If
        the unverified_path will be a new file/path, set must_exist to False


    Returns
    -------
        Path
            unverified_path that passes all verification

    Raises
    ------
    typer.BadParameter
        Raised if the user provides:
            1) An input that cannot be cast to a pathlib.Path
            2) A directory when a file is requested
            3) A file when a directory is requested
            4) If enabled, a path to a file/directory that does not exist

    """
    try:
        path = Path(unverified_path)
    except Exception as e:
        raise typer.BadParameter("Invalid value provided for path") from e

    exists = path.exists()
    is_dir = path.is_dir()
    is_file = path.is_file()

    if not must_exist:
        # is_dir and is_file return false if the directory does not exist, so it does
        # no good to check; if the path does not have to exist, it is new
        return path

    if not exists:
        # Exception chaining!
        raise typer.BadParameter("Path does not exist!") from FileNotFoundError(
            "File or Directory does not exist!"
        )

    if prompt_for_file and is_dir:
        # If the prompt is for a file and the user supplied a directory
        raise typer.BadParameter("File was requested but a directory was provided!")

    if not prompt_for_file and is_file:
        # If the prompt is for a directory (not a file) and the user supplied a file
        raise typer.BadParameter("Directory was requested but a file was provided")

    return path


def prompt_for_path(
    prompt: str, *, is_file: bool = False, must_exist: bool = True
) -> Path | None:
    logger.debug("Asking user to select a path: %s", prompt)
    try:
        return typer.prompt(
            prompt,
            value_proc=lambda path: verify_path(
                path, prompt_for_file=is_file, must_exist=must_exist
            ),
        )
    except typer.Abort:
        logger.debug("User aborted before answering!")

    return None


@app.command()
def prompt_for_path_cli_runner(prompt: Annotated[str, typer.Option()]) -> Path | None:
    return prompt_for_path(prompt)
