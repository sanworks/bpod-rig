"""Module implementing the Pydantic models for any Bpod-specific settings."""

from bpod_rig.config.base import ModelWithMetadata
from pathlib import Path
from pydantic import Field
from typing import Annotated, Optional


def subdir_path_factory(data: dict, addition: str):
    """Function to dynamically create BpodPaths subpaths at validation time.

    Function creates a path in the below form:

    {Parent_Dir}/Machine-{Bpod_ID}/[addition]

    Path components in {} are retrieved from the dictionary of pre-validated data.

    Parameters
    ----------
    data (dict): Dictionary containing all previously validated fields
    addition (str): Addition to join to the end of the path

    Returns
    -------
    (pathlib.Path): combined path in above form
    """
    if data["unique_bpod_dir"] is None:
        return None

    return data["unique_bpod_dir"].joinpath(addition)


def unique_dir_path_factory(data: dict):
    """Function to dynamically create current directory path at validation time.

    Function creates a path in the below form:

    {Parent_Dir}/Machine-{Bpod_ID}

    Path components in {} are retrieved from the dictionary of pre-validated data.

    Parameters
    ----------
    data : dict
        Dictionary containing all previously validated fields

    Returns
    -------
        pathlib.Path : combined path in above form
    """
    if "bpod_id" not in data or "parent_dir" not in data:
        return None

    return data["parent_dir"].joinpath(f"Machine-{data['bpod_id']}")


class BpodPaths(ModelWithMetadata):
    bpod_id: Annotated[
        str,
        Field(
            ...,
            title="Bpod ID",
            description="Unique identifier for each Bpod connected to the system;"
            " doubles as the name for the configuration sub directory name"
            " for this Bpod",
        ),
    ]

    parent_dir: Annotated[
        Path,
        Field(
            ...,
            title="Bpod directory parent directory",
            description="This is the parent directory to this unique Bpod's directory",
        ),
    ]

    unique_bpod_dir: Annotated[
        Path,
        Field(
            title="Directory for this unique Bpod",
            description="Absolute path to the directory for this unique Bpod",
            default_factory=lambda data: unique_dir_path_factory(data),
        ),
    ] = None

    settings_dir: Annotated[
        Optional[Path],
        Field(
            title="Bpod Settings Subdirectory",
            description="Sub directory where Bpod settings files are "
            "stored for this unique Bpod",
            default_factory=lambda data: subdir_path_factory(data, "Settings"),
        ),
    ] = None

    calibration_dir: Annotated[
        Optional[Path],
        Field(
            default_factory=lambda data: subdir_path_factory(data, "Calibration"),
            title="Bpod Calibration Directory",
            description="Local directory where Bpod calibration files are stored.",
        ),
    ] = None

    calibration_files: Annotated[
        Optional[dict[str, Path]],
        Field(
            {},
            title="Bpod calibration files",
            description="Dictionary of calibration files found in the calibration "
            "directory for this Bpod.",
        ),
    ] = None
