import datetime
import logging

import numpy as np
from pydantic import BaseModel, Field, ConfigDict, field_serializer

logger = logging.getLogger(__name__)

class ValveDataClass(BaseModel):
    name: str = Field(alias="ValveName")
    lastdatemodified: datetime.datetime | str = Field(
        serialization_alias="LastDateModified",
        validation_alias="LastDateModified",
        default="",
        description="Modification datetime in ISO format or empty string if not set.",
    )
    coeffs: list[float] = Field(
        alias="Coeffs",
        default=[],
        description="Coefficients for polynomial fitting of durations vs amounts.",
    )
    durations: list[float | int] = Field(
        alias="Durations",
        default=[],
        description="Durations in ms for each dispense, corresponding to the amounts.",
    )
    amounts: list[float | int] = Field(
        alias="Amounts",
        default=[],
        description="Amounts in uL for each dispense, corresponding to the durations.",
    )

    model_config = ConfigDict(
        serialize_by_alias=True, validate_by_name=True, validate_by_alias=True,
    )

    def get_valve_time(self, amount: float) -> float:
        """Get the valve time for a given amount of liquid.

        Parameters
        ----------
        amount : float
            The amount of liquid in mL.

        Returns
        -------
        float
            The duration in ms for the given amount.
        """
        if len(self.coeffs) == 0:
            raise ValueError("Coefficients are not set. Please add measurements first.")
        duration = np.polyval(self.coeffs, amount)
        logger.debug(
            "%s calculated valve time: %s ms for amount: %s mL",
            self.name,
            duration,
            amount,
        )
        return float(duration)

    def add_measurement(self, duration: float, amount: float) -> None:
        """Add a measurement to the valve data.

        Parameters
        ----------
        duration : float
            The duration of the dispense in ms.
        amount : float
            The amount of liquid dispensed mL.
        """
        self.amounts.append(amount)
        self.durations.append(duration)
        logger.debug("Added measurement: amount = %s, duration = %s", amount, duration)
        self.lastdatemodified = datetime.datetime.now()
        self._update_coeffs()

    def remove_measurement(self, value: int | float, method: str = "index") -> None:
        """Remove a measurement from the valve data.

        Parameters
        ----------
        value : int | float
            The index or duration to remove.
        method : str, optional (default = 'index')
            How to use value to find the measurement to remove. 'index' to remove by index,
            'duration' to remove by duration value (assuming unique duration).
        """
        if method == "duration":
            if value in self.durations:
                # Throw error if value is in durations multiple times
                if self.durations.count(value) > 1:
                    raise ValueError(
                        "Duration value is present multiple times. Index must be specified."
                    )
                index = self.durations.index(value)
                del self.amounts[index]
                del self.durations[index]
                logger.debug("Removed measurement by duration: %s", value)
            else:
                raise ValueError("Duration value not found in durations list.")
        elif method == "index":
            if 0 <= value < len(self.amounts):
                del self.amounts[value]
                del self.durations[value]
                logger.debug("Removed measurement by index: %s", value)
            else:
                raise IndexError("Index out of range for amounts and durations lists.")
        else:
            raise ValueError(f"Unknown method for removing measurement: {method}")
        self.lastdatemodified = datetime.datetime.now()
        self._update_coeffs()

    def _update_coeffs(self) -> None:
        """Update the polynomial coefficients based on current measurements."""
        if len(self.amounts) < 2:
            self.coeffs = []
            return
        # TODO: 1 value assumes intercept at 0?
        elif len(self.amounts) == 2:
            # If only two measurements, use linear fit
            order = 1
        else:
            # Fit a polynomial of degree 2
            order = 2
        self.coeffs = np.polyfit(self.amounts, self.durations, order).tolist()

    @field_serializer("lastdatemodified")
    def serialize_datetime(self, dt: datetime.datetime, _info):
        if isinstance(dt, str): # if uncalibrated it is an empty string
            return dt
        return dt.isoformat(timespec="seconds")


class ValveManagerMetaData(BaseModel):
    modification_datetime: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="Time of when the valve data was last saved to json file.",
    )
    COM: str = ""

    @field_serializer("modification_datetime")
    def serialize_datetime(self, modification_datetime: datetime.datetime, _info):
        return modification_datetime.isoformat(timespec="seconds")


class ValveDataManagerClass(BaseModel):
    metadata: ValveManagerMetaData = Field(default_factory=ValveManagerMetaData)
    valve_datas: list[ValveDataClass] = Field(
        alias="ValveDatas", default=[], description="Array of valve data objects."
    )

    model_config = ConfigDict(serialize_by_alias=True, validate_by_name=True)

    def get_valve(self, valvename: str) -> ValveDataClass:
        """Get a valve by name.

        Parameters
        ----------
        valvename : str
            The name of the valve to retrieve.

        Returns
        -------
        ValveDataClass
        """
        # Check if the valve exists in the ValveDatas list
        if valvename in self.valve_names:
            # check if there are two valves with same name, raise error if so
            if sum(name == valvename for name in self.valve_names) > 1:
                raise KeyError(f"Multiple valves with name '{valvename}' found.")
            return next(valve for valve in self.valve_datas if valve.name == valvename)
        else:
            raise KeyError(f"Valve '{valvename}' not found in valve manager.")

    def create_valve(self, valvename: str) -> None:
        """Create a new valve with the given name."""
        if valvename in self.valve_names:
            raise KeyError(f"Valve '{valvename}' already exists.")
        self.valve_datas.append(ValveDataClass(name=valvename))  # noqa: aliasing with pydantic can cause type check issues
        logger.debug(f"Created new valve: {valvename}")

    @property
    def n_valves(self) -> int:
        """Get the number of valves in the manager."""
        return len(self.valve_datas)

    @property
    def valve_names(self) -> list[str]:
        """Get a list of valve names."""
        return list(valve.name for valve in self.valve_datas)

    def to_json(self, machineid: str = None) -> str:
        """Convert the ValveDataManagerPydantic to JSON string.

        Parameters
        ----------
        machineid : str, optional
            The COM port or machine ID to set in the metadata.
        """
        if machineid is not None:
            if not isinstance(machineid, str):
                raise ValueError("machineid must be a string.")

            # check if the COM is changing
            if (self.metadata.COM != "") & (self.metadata.COM != machineid):
                logger.warning(
                    "COM port of liquid calibration file is changing from %s to %s", self.metadata.COM, machineid
                )
            self.metadata.COM = machineid
        self.metadata.modification_datetime = datetime.datetime.now()
        return self.model_dump_json(indent=2)
