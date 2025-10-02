import pytest
import urllib.request

from bpod_rig.calibration.liquid import utils, populate_examples
from bpod_rig.calibration.liquid.models import ValveData, ValveDataManager


class TestValveDataClass:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.valve = ValveData(ValveName="Test Valve")

    def test_init_alias(self):
        # Test that alias works correctly
        # type checker may complain about this because of pydantic aliasing
        assert ValveData(name="attrname").name == "attrname"  # noqa: Pydantic's validation aliases raises Unexpected Argument
        assert ValveData(ValveName="aliasname").name == "aliasname"

    def test_add_measurement(self):
        self.valve.add_measurement(10, 1.0)
        assert len(self.valve.amounts) == 1
        assert len(self.valve.durations) == 1

    def test_get_valve_time(self):
        self.valve.add_measurement(10, 1.0)
        self.valve.add_measurement(20, 2.0)
        duration = self.valve.get_valve_time(1.0)
        assert duration == pytest.approx(10)

    def test_remove_measurement_by_index(self):
        self.valve.add_measurement(10, 1.0)
        self.valve.remove_measurement(0)
        assert len(self.valve.amounts) == 0

    def test_remove_measurement_by_duration(self):
        self.valve.add_measurement(10, 1.0)
        self.valve.remove_measurement(10, method="duration")
        assert len(self.valve.amounts) == 0

    def test_remove_measurement_invalid_index(self):
        self.valve.add_measurement(10, 1.0)
        self.valve.add_measurement(20, 2.0)
        self.valve.remove_measurement(0)
        with pytest.raises(IndexError):
            self.valve.remove_measurement(5)

    def test_remove_measurement_invalid_duration(self):
        self.valve.add_measurement(10, 1.0)
        self.valve.add_measurement(20, 2.0)
        with pytest.raises(ValueError):
            self.valve.remove_measurement(15, method="duration")

    def test_remove_measurement_duplicate_duration(self):
        self.valve.add_measurement(10, 1.0)
        self.valve.add_measurement(10, 2.0)
        with pytest.raises(ValueError):
            self.valve.remove_measurement(10, method="duration")

    def test_no_coeffs_with_insufficient_data(self):
        self.valve.add_measurement(10, 1.0)
        assert len(self.valve.coeffs) == 0
        with pytest.raises(ValueError):
            self.valve.get_valve_time(1.0)
        self.valve.add_measurement(20, 2.0)
        assert self.valve.coeffs is not None


class TestValveDataManagerClass:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.manager = ValveDataManager()
        self.manager.create_valve("Test Valve")
        dummy = utils.create_empty_valve_data_manager()
        populate_examples.add_dummy_measurements(dummy)
        self.dummy = dummy

    def test_create_valve(self):
        assert self.manager.n_valves == 1
        assert "Test Valve" in self.manager.valve_names

    def test_get_valve(self):
        valve = self.manager.get_valve("Test Valve")
        assert isinstance(valve, ValveData)

    def test_measurements(self):
        """Test that the default values are behaving as expected."""
        liquid_amount = 15

        valve = "Valve1"
        expected_duration = 0.0758261 * 1000
        duration = self.dummy.get_valve(valve).get_valve_time(liquid_amount)
        assert duration == pytest.approx(expected_duration, abs=0.001)

        valve = "Valve3"
        expected_duration = 0.1102557 * 1000
        duration = self.dummy.get_valve(valve).get_valve_time(liquid_amount)
        assert duration == pytest.approx(expected_duration, abs=0.001)


class TestGen2CalibrationFile:
    """Test loading a calibration file from the Bpod_Gen2 (MATLAB) repo."""

    @pytest.fixture(scope="class")
    def jsontext(self):
        return (
            urllib.request.urlopen(
                "https://raw.githubusercontent.com/sanworks/Bpod_Gen2/refs/heads/develop/Examples/Example%20Calibration%20Files/LiquidCalibration.json"
            )
            .read()
            .decode()
        )

    def test_load_calibration_file(self, jsontext):
        loaded_valves = ValveDataManager.model_validate_json(jsontext)
        assert isinstance(loaded_valves, ValveDataManager)
        assert loaded_valves.n_valves >= 1
        assert "Valve1" in loaded_valves.valve_names

    def test_valve_modtime(self, jsontext):
        valvemanager = ValveDataManager.model_validate_json(jsontext)
        assert not utils.check_valvemanager_user_updated(valvemanager)
        newvalve = ValveDataManager.model_validate_json(valvemanager.to_json())
        assert utils.check_valvemanager_user_updated(newvalve)


class TestValveDataManagerJSON:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.manager = utils.create_empty_valve_data_manager()
        populate_examples.add_dummy_measurements(self.manager)
        self.json_str = self.manager.to_json()
        self.loaded_manager = ValveDataManager.model_validate_json(self.json_str)

    def test_json_round_trip(self):
        assert self.manager.n_valves == self.loaded_manager.n_valves
        assert self.manager.valve_names == self.loaded_manager.valve_names
        for valve_name in self.manager.valve_names:
            original_valve = self.manager.get_valve(valve_name)
            loaded_valve = self.loaded_manager.get_valve(valve_name)
            assert original_valve.amounts == loaded_valve.amounts
            assert original_valve.durations == loaded_valve.durations
            assert original_valve.coeffs == loaded_valve.coeffs
