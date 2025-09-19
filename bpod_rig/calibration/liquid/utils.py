"""Liquid calibration data management and calibration routines."""

import datetime
import logging
import numpy as np

from bpod_rig.calibration.liquid.models import ValveData, ValveDataManager

logger = logging.getLogger(__name__)


def create_empty_valve_data_manager(
    source: str = "statemachine",
    n_valves: int = 8,
) -> ValveDataManager:
    """Create an empty valve manager with 8 valves."""
    valvemanager = ValveDataManager()
    if source == "statemachine":
        for index in range(n_valves):
            valvemanager.create_valve(f"Valve{index + 1}")
    elif source == "portarray":
        for index in range(n_valves):
            for port_array in range(4):
                valvemanager.create_valve(f"PA{port_array + 1}_{index + 1}")
    else:
        raise ValueError(f"Unknown source for valve names: {source}")

    return valvemanager


def check_valvemanager_user_updated(valvemanager: ValveDataManager) -> bool:
    """Check if the user has updated the valve manager has been updated from the example.

    This is determined by checking if any valve has a modification date later than the
    origin date of 2000-01-01.

    Parameters
    ----------
    valvemanager : ValveDataManager
        The valve manager to check.

    Returns
    -------
    bool
        True if any valve has measurements, False otherwise.
    """
    return valvemanager.metadata.modification_datetime > datetime.datetime(2000, 1, 1)


def suggest_duration(
    valveobject: ValveData,
    range_low: float,
    range_high: float,
) -> float:
    """Suggest a duration for a given valve and range.

    Parameters
    ----------
    valveobject : ValveData
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
    midpoint_value = (
        sorted_values[max_distance_pos - 1]
        + (sorted_values[max_distance_pos] - sorted_values[max_distance_pos - 1]) / 2
    )
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


def calculate_ranged_amounts(
    amounts: np.array, range_low: float, range_high: float
) -> list[float]:
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
    amounts_vector = amounts_vector[startpoint : endpoint + 1]
    return amounts_vector


def check_com(valvemanager: ValveDataManager, com_port: str) -> str:
    """Check if the COM port in the valve manager matches the given COM port.

    Parameters
    ----------
    valvemanager : ValveDataManager
        The valve manager to check.
    com_port : str
        The COM port to check against.

    Returns
    -------
    str
        'yes' if the COM ports match, 'no' if it's different, 'unknown' otherwise.
    """
    valvecom = valvemanager.metadata.COM
    if valvecom == "":  # e.g. uncalibrated
        return "unknown"
    if valvecom == com_port:
        return "yes"
    else:
        return "no"
