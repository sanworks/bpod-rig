import unittest
import urllib.request

from bpod_rig.calibration.liquid import liquid
from bpod_rig.calibration.liquid.models import ValveDataClass, ValveDataManagerClass


class TestValveDataClass(unittest.TestCase):
    def setUp(self):
        self.valve = ValveDataClass(ValveName="Test Valve")

    def test_init_alias(self):
        # Test that alias works correctly
        # type checker may complain about this because of pydantic aliasing
        self.assertEqual(ValveDataClass(name="attrname").name, "attrname")
        self.assertEqual(ValveDataClass(ValveName="aliasname").name, "aliasname")

    def test_add_measurement(self):
        self.valve.add_measurement(10, 1.0)
        self.assertEqual(len(self.valve.amounts), 1)
        self.assertEqual(len(self.valve.durations), 1)

    def test_get_valve_time(self):
        self.valve.add_measurement(10, 1.0)
        self.valve.add_measurement(20, 2.0)
        duration = self.valve.get_valve_time(1.0)
        self.assertAlmostEqual(duration, 10)

    def test_remove_measurement_by_index(self):
        self.valve.add_measurement(10, 1.0)
        self.valve.remove_measurement(0)
        self.assertEqual(len(self.valve.amounts), 0)

    def test_remove_measurement_by_duration(self):
        self.valve.add_measurement(10, 1.0)
        self.valve.remove_measurement(10, method="duration")
        self.assertEqual(len(self.valve.amounts), 0)

    def test_remove_measurement_invalid_index(self):
        self.valve.add_measurement(10, 1.0)
        self.valve.add_measurement(20, 2.0)
        self.valve.remove_measurement(0)
        with self.assertRaises(IndexError):
            self.valve.remove_measurement(5)

    def test_remove_measurement_invalid_duration(self):
        self.valve.add_measurement(10, 1.0)
        self.valve.add_measurement(20, 2.0)
        with self.assertRaises(ValueError):
            self.valve.remove_measurement(15, method="duration")

    def test_remove_measurement_duplicate_duration(self):
        self.valve.add_measurement(10, 1.0)
        self.valve.add_measurement(10, 2.0)
        with self.assertRaises(ValueError):
            self.valve.remove_measurement(10, method="duration")

    def test_no_coeffs_with_insufficient_data(self):
        self.valve.add_measurement(10, 1.0)
        self.assertEqual(len(self.valve.coeffs), 0)
        with self.assertRaises(ValueError):
            self.valve.get_valve_time(1.0)
        self.valve.add_measurement(20, 2.0)
        self.assertIsNotNone(self.valve.coeffs)


class TestValveDataManagerClass(unittest.TestCase):
    def setUp(self):
        self.manager = ValveDataManagerClass()
        self.manager.create_valve("Test Valve")
        dummy = liquid.create_empty_valve_data_manager()
        liquid.add_dummy_measurements(dummy)
        self.dummy = dummy

    def test_create_valve(self):
        self.assertEqual(self.manager.n_valves, 1)
        self.assertIn("Test Valve", self.manager.valve_names)

    def test_get_valve(self):
        valve = self.manager.get_valve("Test Valve")
        self.assertIsInstance(valve, ValveDataClass)

    def test_measurements(self):
        """Test that the default values are behaving as expeted."""
        liquid_amount = 15

        valve = "Valve1"
        expected_duration = 0.0758261 * 1000
        duration = self.dummy.get_valve(valve).get_valve_time(liquid_amount)
        self.assertAlmostEqual(duration, expected_duration, places=3)

        valve = "Valve3"
        expected_duration = 0.1102557 * 1000
        duration = self.dummy.get_valve(valve).get_valve_time(liquid_amount)
        self.assertAlmostEqual(duration, expected_duration, places=3)


class TestGen2CalibrationFile(unittest.TestCase):
    """Test loading a calibration file from the Bpod_Gen2 (MATLAB) repo."""

    @classmethod
    def setUpClass(cls):
        super(TestGen2CalibrationFile, cls).setUpClass()
        url = "https://raw.githubusercontent.com/sanworks/Bpod_Gen2/refs/heads/develop/Examples/Example%20Calibration%20Files/LiquidCalibration.json"
        cls.jsontext = urllib.request.urlopen(url).read().decode()

    def test_load_calibration_file(self):
        loaded_valves = ValveDataManagerClass.model_validate_json(self.jsontext)
        self.assertIsInstance(loaded_valves, ValveDataManagerClass)
        self.assertGreaterEqual(loaded_valves.n_valves, 1)
        self.assertIn("Valve1", loaded_valves.valve_names)

    def test_valve_modtime(self):
        valvemanager = ValveDataManagerClass.model_validate_json(self.jsontext)
        self.assertFalse(liquid.check_valvemanager_user_updated(valvemanager))
        newvalve = ValveDataManagerClass.model_validate_json(valvemanager.to_json())
        self.assertTrue(liquid.check_valvemanager_user_updated(newvalve))


class TestValveDataManagerJSON(unittest.TestCase):
    def setUp(self):
        self.manager = liquid.create_empty_valve_data_manager()
        liquid.add_dummy_measurements(self.manager)
        self.json_str = self.manager.to_json()
        self.loaded_manager = ValveDataManagerClass.model_validate_json(self.json_str)

    def test_json_round_trip(self):
        self.assertEqual(self.manager.n_valves, self.loaded_manager.n_valves)
        self.assertEqual(self.manager.valve_names, self.loaded_manager.valve_names)
        for valve_name in self.manager.valve_names:
            original_valve = self.manager.get_valve(valve_name)
            loaded_valve = self.loaded_manager.get_valve(valve_name)
            self.assertEqual(original_valve.amounts, loaded_valve.amounts)
            self.assertEqual(original_valve.durations, loaded_valve.durations)
            self.assertEqual(original_valve.coeffs, loaded_valve.coeffs)


class TestSuggestDuration(unittest.TestCase):
    def setUp(self):
        self.valve = ValveDataClass(ValveName="Test Valve")
        self.range_low = 2
        self.range_high = 10
        self.suggest_duration = lambda: liquid.suggest_duration(
            self.valve, self.range_low, self.range_high
        )

    def test_no_measures(self):
        self.assertEqual(self.suggest_duration(), 48)

    def test_one_measure(self):
        self.valve.add_measurement(57, 7.5)
        self.assertEqual(self.suggest_duration(), 36)

    def test_two_measures(self):
        self.valve.add_measurement(22, 2)
        self.valve.add_measurement(66, 9.5)
        self.assertAlmostEqual(self.suggest_duration(), 44.0, places=3)
