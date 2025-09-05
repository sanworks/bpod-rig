"""Liquid calibration data management and calibratino routines."""
import datetime
import logging
from pydantic import BaseModel, Field, ConfigDict, field_serializer
import numpy as np

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
            The duration of the dispense.
        amount : float
            The amount of liquid dispensed.
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
            The amount or duration to remove.
        method : str, optional (default = 'index')
            How to use value to find the measurement to remove. 'index' to remove by index,
            'duration' to remove by duration value.
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
        if len(self.amounts) < 2:
            self.coeffs = []
            return
        # TODO: 1 value assumes intercept at 0?
        elif len(self.amounts) == 2:
            # If only two measurements, use linear fit
            order = 1
        else:
            order = 2
        # Example: Fit a polynomial of degree 2
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


def create_empty_valve_data_manager(
        source: str = 'statemachine',
        n_valves: int = 8,
) -> ValveDataManagerClass:
    """Create an empty valve manager with 8 valves."""
    valvemanager = ValveDataManagerClass()
    if source == 'statemachine':
        for index in range(n_valves):
            valvemanager.create_valve(f"Valve{index + 1}")
    elif source == 'portarray':
        for index in range(n_valves):
            for port_array in range(4):
                valvemanager.create_valve(f"PA{port_array + 1 }_{index + 1}")
    else:
        raise ValueError(f"Unknown source for valve names: {source}")

    return valvemanager


def add_dummy_measurements(valvemanager: ValveDataManagerClass) -> None:
    """Add dummy measurements to the valves in manager."""
    origin_date = datetime.datetime(2000, 1, 1)
    valve1 = valvemanager.get_valve("Valve1")
    valve1.add_measurement(22, 2)
    valve1.add_measurement(66, 9.5)
    valve1.add_measurement(44, 5)
    valve1.add_measurement(57, 7.5)
    valve1.add_measurement(34, 3.5)
    valve1.lastdatemodified = origin_date

    valve3 = valvemanager.get_valve("Valve3")
    valve3.add_measurement(22, 1.5)
    valve3.add_measurement(46, 5.5)
    valve3.add_measurement(59, 7.5)
    valve3.add_measurement(35, 3.5)
    valve3.add_measurement(66, 8.5)
    valve3.lastdatemodified = origin_date

    valvemanager.metadata.modification_datetime = origin_date

def create_default_json() -> str:
    """Produce a default valve JSON string with 8 valves and dummy measurements."""
    dummy = create_empty_valve_data_manager()
    add_dummy_measurements(dummy)
    jsontext = dummy.to_json(machineid=None)
    # replace modification datetime with a fixed date for consistency
    jsontext = jsontext.replace(
        dummy.metadata.modification_datetime.isoformat(timespec="seconds"),
        "2000-01-01T00:00:00",
    )
    return jsontext

def check_valvemanager_user_updated(valvemanager: ValveDataManagerClass) -> bool:
    """Check if the user has updated the valve manager has been updated from the example.

    This is determined by checking if any valve has a modification date later than the
    origin date of 2000-01-01.

    Parameters
    ----------
    valvemanager : ValveDataManagerClass
        The valve manager to check.

    Returns
    -------
    bool
        True if any valve has measurements, False otherwise.
    """
    return valvemanager.metadata.modification_datetime > datetime.datetime(2000, 1, 1)


def suggest_duration(
        valveobject: ValveDataClass,
        range_low: float,
        range_high: float,
) -> float:
    """Suggest a duration for a given valve and range.

    Parameters
    ----------
    valveobject : ValveDataClass
        The valve object to use for the suggestion.
    range_low : float
        The lower bound of microliters (uL) for the range.
    range_high : float
        The upper bound of microliters (uL) for the range.

    Returns
    -------
    float
        The suggested duration in ms.
    """
    if len(valveobject.durations) >= 1:
        durations = np.array(valveobject.durations)
        amounts = np.array(valveobject.amounts)
    else:
        durations = np.array([])
        amounts = np.array([])

    n_measurements = len(durations)

    if n_measurements >= 2:  # Use curve fit to predict next measurement
        amounts_vector = calculate_ranged_amounts(amounts, range_low, range_high)
        suggested_amount = calculate_largest_gap_midpoint(amounts_vector)
        suggested_duration_ms = valveobject.get_valve_time(suggested_amount)
    elif n_measurements == 1:
        # Use a linear estimate
        suggested_duration_ms = linearly_suggest_duration(
            amounts[0], durations[0], range_low, range_high
            )
    else:
        # Use an estimate of the middle of the range based on range and our experience with
        # the CSHL configuration (nResearch pinch valves, silastic tubing, specs in Bpod literature)
        suggested_duration_ms = (range_high + range_low) * 4
    return suggested_duration_ms


def calculate_largest_gap_midpoint(sorted_values: list[float]) -> float:
    """Calculate the midpoint of the largest gap in a sorted list of values."""
    distances = np.zeros(len(sorted_values))
    for y in range(1, len(sorted_values)):
        distances[y] = abs(sorted_values[y] - sorted_values[y - 1])
    max_distance_pos = np.argmax(distances)
    midpoint_value = sorted_values[max_distance_pos - 1] + (
            sorted_values[max_distance_pos] - sorted_values[max_distance_pos - 1]
    ) / 2
    return midpoint_value


def linearly_suggest_duration(
        amount: float | np.typing.ArrayLike,
        duration: float | np.typing.ArrayLike,
        range_low: float,
        range_high: float,
) -> float:
    """Suggest a duration based on a single measurement and a range."""
    ul_per_ms = float(amount / duration)
    if (amount < range_low) or (amount > range_high):
        target_amount = (range_high - range_low) / 2
    else:
        bottom_part = amount - range_low
        top_part = range_high - amount
        if bottom_part > top_part:
            target_amount = range_low + (bottom_part / 2)
        else:
            target_amount = range_high - (top_part / 2)
    suggested_duration = round(target_amount / ul_per_ms)
    return suggested_duration


def calculate_ranged_amounts(amounts: np.array, range_low: float, range_high: float) -> list[float]:
    """Calculate a sorted list of amounts within a given range, including the range bounds."""
    amounts_vector = amounts.tolist()
    if range_low not in amounts:
        amounts_vector.append(range_low)
    if range_high not in amounts:
        amounts_vector.append(range_high)

    # take only values within range
    amounts_vector = sorted(amounts_vector)
    startpoint = amounts_vector.index(range_low)
    endpoint = amounts_vector.index(range_high)
    amounts_vector = amounts_vector[startpoint: endpoint + 1]
    return amounts_vector

def check_COM(valvemanager: ValveDataManagerClass, com_port: str) -> str:
    """Check if the COM port in the valve manager matches the given COM port.

    Parameters
    ----------
    valvemanager : ValveDataManagerClass
        The valve manager to check.
    com_port : str
        The COM port to check against.

    Returns
    -------
    str
        'yes' if the COM ports match, 'no' if it's different, 'unknown' otherwise.
    """
    valvecom = valvemanager.metadata.COM
    if valvecom == "": # e.g. uncalibrated
        return 'unknown'
    if valvecom == com_port:
        return 'yes'
    else:
        return 'no'

class PendingValve(ValveDataClass):
    pending_durations: list[float] = Field(
        default=[],
        description="List of durations that are pending calibration measurements.",
    )

    valve_controller: str = Field(
        default="unknown",
        description="The controlling hardware of the valve (e.g., 'StateMachine', 'PortArray').",
    )

    def __init__(self, **data):
        super().__init__(**data)
        if self.name.startswith("PA"):
            self.valve_controller = "PortArray"
        else:
            self.valve_controller = "StateMachine"

    def get_calibration_run_info(self) -> float:
        pass


class PendingMeasurementsManager:
    _valvemanager: ValveDataManagerClass
    valves: list[PendingValve]

    def __init__(self, valvemanager: ValveDataManagerClass):
        self._valvemanager = valvemanager
        self.valves = [PendingValve(ValveName=valve.name) for valve in valvemanager.valve_datas]

    def get_pending(self, valvename: str) -> list[float]:
        if valvename not in self._valvemanager.valve_names:
            raise KeyError(f"Valvename '{valvename}' not found in manager.")

        return next(valve for valve in self.valves if valve.name == valvename).pending_durations

    def add_pending(self, valvename: str, duration: float) -> None:
        if duration in self.get_pending(valvename):
            raise ValueError("Duration already pending.")
        if duration in self._valvemanager.get_valve(valvename).durations:
            raise ValueError("Duration already exists in valve calibration.")

        self.get_pending(valvename).append(duration)

    def remove_pending(self, valvename: str, duration: float) -> None:
        if duration not in self.get_pending(valvename):
            raise ValueError("Duration for completed measurement is not pending.")

        self.get_pending(valvename).remove(duration)

    def complete_measurement(self, valvename: str, duration: float, amount: float) -> None:
        self.remove_pending(valvename, duration)
        self._valvemanager.get_valve(valvename).add_mesurement(duration, amount)

def run_calibration(
        pending_manager: PendingMeasurementsManager,
        n_pulses: int,
        pulse_interval: float = 0.2,
        pulse_set_pause: float = 0.5,
        verbose: bool = True,
) -> None:
    """Run a calibration sequence using Bpod state machine.

    Parameters
    ----------

    """

    from bpod_core.fsm import StateMachine

    fsm = StateMachine()

    fsm.add_state(
        name='Port1Light',
        timer=1,
        state_change_conditions={'BNC1_High': 'Port2Light'},
        output_actions={'PWM1': 255},
    )
    fsm.add_state(
        name='Port2Light',
        timer=1,
        state_change_conditions={'Tup': '>exit'},
        output_actions={'PWM2': 255},
    )
