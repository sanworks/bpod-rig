"""Liquid calibration data management and calibratino routines."""
import datetime
import logging
from pydantic import Field
import numpy as np

from .models import ValveDataClass, ValveDataManagerClass

logger = logging.getLogger(__name__)


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
