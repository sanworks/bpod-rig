import datetime
import unittest

from bpod_rig.calibration.liquid import utils
from bpod_rig.calibration.liquid.models import ValveData, ValveDataManager


class TestSuggestDuration(unittest.TestCase):
    def setUp(self):
        self.valve = ValveData(ValveName="Test Valve")
        self.range_low = 2
        self.range_high = 10
        self.suggest_duration = lambda: utils.suggest_duration(
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


class TestCheckValveManagerUserUpdate(unittest.TestCase):
    def setUp(self):
        self.manager = ValveDataManager()

    def test_earlier(self):
        self.manager.metadata.modification_datetime = datetime.datetime(1999, 1, 1)
        self.assertFalse(utils.check_valvemanager_user_updated(self.manager))

    def test_later(self):
        self.manager.create_valve("Valve1")
        self.manager.get_valve("Valve1").add_measurement(15, 20)
        self.assertTrue(utils.check_valvemanager_user_updated(self.manager))

    def test_equal(self):
        self.manager.metadata.modification_datetime = datetime.datetime(2000, 1, 1)
        self.assertFalse(utils.check_valvemanager_user_updated(self.manager))

    def test_dummy(self):
        from bpod_rig.calibration.liquid.populate_examples import create_default_json

        manager = ValveDataManager.model_validate_json(create_default_json())
        self.assertFalse(utils.check_valvemanager_user_updated(manager))


class TestCheckCOM(unittest.TestCase):
    def setUp(self):
        self.manager = ValveDataManager()
        self.manager.metadata.COM = "COM3"

    def test_matching(self):
        self.assertEqual(utils.check_COM(self.manager, "COM3"), "yes")

    def test_no_match(self):
        self.assertEqual(utils.check_COM(self.manager, "COM4"), "no")

    def test_unknown(self):
        self.manager.metadata.COM = ""
        self.assertEqual(utils.check_COM(self.manager, "COM3"), "unknown")
