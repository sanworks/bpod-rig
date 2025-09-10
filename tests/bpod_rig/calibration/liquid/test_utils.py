import unittest

from bpod_rig.calibration.liquid import utils
from bpod_rig.calibration.liquid.models import ValveData


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
