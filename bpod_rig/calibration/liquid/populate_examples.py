"""Create the example liquid calibration JSON with 8 valves and dummy measurements."""

import datetime
from pathlib import Path

from bpod_rig.examples import calibration as example_folder
from bpod_rig.calibration.liquid.models import ValveDataManager
from bpod_rig.calibration.liquid.utils import create_empty_valve_data_manager


def add_dummy_measurements(valvemanager: ValveDataManager) -> None:
    """Add dummy measurements to the valves in manager.

    Modifies the data in place.
    Uses 2000-01-01 as the origin date for the data.

    Examples
    --------
    >>> dummy_liquid_manager = create_empty_valve_data_manager()
    >>> add_dummy_measurements(dummy_liquid_manager)
    """
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
    return jsontext.replace(
        dummy.metadata.modification_datetime.isoformat(timespec="seconds"),
        "2000-01-01T00:00:00",
    )


def main():
    """Create the example liquid calibration JSON in the example folder."""
    example_json = create_default_json()
    example_path = Path(example_folder.__path__[0]) / "LiquidCalibration.json"
    example_path.write_text(example_json)


if __name__ == "__main__":
    main()
