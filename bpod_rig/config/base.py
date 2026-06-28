"""Base classes for configuration classes."""

import datetime
import logging
import pathlib
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PastDate,
    field_validator,
    model_validator,
)

from bpod_rig import log
from bpod_rig.IO import json_handler

logger = log.get_logger(__name__)


class SettingsMetadata(BaseModel):
    model_config = ConfigDict()

    creation_date: Annotated[
        datetime.date | PastDate,
        Field(
            title="Settings Creation Date",
            description="Date that this settings model was instantiated",
        ),
    ] = datetime.date.today()

    modified_datetime: Annotated[
        datetime.datetime | PastDate | None,  # Optional, but can be either type
        Field(
            None,
            title="Settings Save Date and Time",
            description="Date and time that this settings model was saved or updated.",
        ),
    ] = None

    username: Annotated[
        str | None,
        Field(
            min_length=1,
            max_length=128,
            title="Username of settings creator",
            description="Username of the creator of this settings model.",
        ),
    ] = "BpodUser"

    # noinspection PyNestedDecorators
    @field_validator("creation_date", mode="after")
    @classmethod
    def validate_nonfuture(cls, value: datetime.date) -> datetime.date:
        if value is not None and value > datetime.date.today():
            raise ValueError(f"Provided creation_date {value} cannot be in the future!")
        return value

    # noinspection PyNestedDecorators
    @field_validator("modified_datetime", mode="after")
    @classmethod
    def validate_nonfuture_datetime(cls, value: datetime.datetime) -> datetime.datetime:
        if value is not None and value > datetime.datetime.now():
            raise ValueError(
                f"Provided modified_datetime {value} cannot be in the future!"
            )
        return value


class ModelWithMetadata(BaseModel):
    model_config = ConfigDict()

    metadata: Annotated[
        SettingsMetadata,
        Field(title="Model metadata", default_factory=SettingsMetadata),
    ]

    # noinspection PyNestedDecorators
    @model_validator(mode="before")
    @classmethod
    def forward_username(cls, data: object) -> object:
        """Bring username into metadata.

        For simplicity, allow the user to pass username to the SystemSettings
        constructor for instantiating a SettingsMetadata object.

        If the user provides a value for "metadata", we will assume
        they passed an initialized and validated SettingsMetadata object. If not,
        the fields default validation will catch it. If not and they provide
        "username", instantiate a SettingsMetadata object with the custom username
        and place it in the kwargs dict.

        Parameters
        ----------
        data : object
            Unparsed kwargs dict passed to the SystemSettings constructor

        Returns
        -------
        object
            Kwargs dict modified to be passed to the SystemSettings constructor
        """
        if not isinstance(data, dict):
            return data

        if "metadata" not in data and "username" in data:
            # if the user passed in a dictionary for metadata, we will just forward it
            # otherwise, forward the "username" field to SettingsMetadata and return it
            username = data["username"]
            if isinstance(username, str):
                data["metadata"] = SettingsMetadata(username=username)
        return data

    def update_modification_time(self) -> None:
        """
        Update metadata modified_datetime field.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        time = datetime.datetime.now()
        logger.debug("Setting modification time for [%s] to %s", self, time)
        self.metadata.modified_datetime = time

    def save_model(self, save_directory: pathlib.Path, filename: str) -> pathlib.Path:
        """Dump model to JSON and save it to disk.

        Parameters
        ----------
        save_directory : pathlib.Path
            Directory to save the JSON file to
        filename : str
            Name of saved file without the .json suffix

        Returns
        -------
            None
        """
        model_as_json = self.model_dump_json(indent=2)
        return json_handler.write_json(model_as_json, save_directory, filename)


class ModuleBase(ModelWithMetadata):
    name: Annotated[
        str,
        Field(
            title="Module Name",
            description="Name of module associated with this configuration",
        ),
    ]
    USB_port: Annotated[
        str, Field(title="USB Port", description="Last used USB port for this module")
    ]
