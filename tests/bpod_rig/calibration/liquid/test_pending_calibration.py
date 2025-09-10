import unittest

from bpod_core.fsm import StateMachine

from bpod_rig.calibration.liquid import pending_calibration
from bpod_rig.calibration.liquid import utils, populate_examples


class test_PendingValve(unittest.TestCase):
    def setUp(self):
        self.pending_valve = pending_calibration.PendingValve(ValveName="Valve3")

    def test_valve_controller_assignment(self):
        valve1 = pending_calibration.PendingValve(ValveName="PA1")
        valve2 = pending_calibration.PendingValve(ValveName="Valve1")
        self.assertEqual(valve1.valve_controller, "PortArray")
        self.assertEqual(valve2.valve_controller, "StateMachine")

    def test_unrecognied_controller_assignment(self):
        with self.assertRaises(ValueError):
            valve1 = pending_calibration.PendingValve(ValveName="HeartValve")

    def test_ispending(self):
        valve = pending_calibration.PendingValve(ValveName="Valve1")
        self.assertFalse(valve.is_pending)
        valve = pending_calibration.PendingValve(ValveName="Valve1")
        valve.pending_durations.append(20)
        self.assertTrue(valve.is_pending)


class test_PendingMeasurementsManager(unittest.TestCase):
    def setUp(self):
        self.valvemanager = utils.create_empty_valve_data_manager()
        populate_examples.add_dummy_measurements(self.valvemanager)
        self.manager = pending_calibration.PendingMeasurementsManager(self.valvemanager)

    def test_get_pending_initial(self):
        self.assertEqual(self.manager.get_pending("Valve1"), [])
        self.assertEqual(self.manager.get_pending("Valve2"), [])

    def test_get_pending_invalid_valve(self):
        with self.assertRaises(KeyError):
            self.manager.get_pending("InvalidValve")

    def test_add_pending(self):
        self.manager.add_pending("Valve1", 10.0) # valve with values
        self.assertIn(10.0, self.manager.get_pending("Valve1"))
        self.manager.add_pending("Valve2", 10.0) # valve without values
        self.assertIn(10.0, self.manager.get_pending("Valve2"))

    def test_add_pending_duplicate(self):
        self.manager.add_pending("Valve1", 10.0)
        with self.assertRaises(ValueError):
            self.manager.add_pending("Valve1", 10.0)

    def test_remove_pending(self):
        self.manager.add_pending("Valve1", 10.0)
        self.manager.remove_pending("Valve1", 10.0)
        self.assertNotIn(10.0, self.manager.get_pending("Valve1"))

    def test_remove_pending_nonexistent(self):
        with self.assertRaises(ValueError):
            self.manager.remove_pending("Valve1", 10.0)

    def test_complete_measurement(self):
        self.manager.add_pending("Valve2", 10.0)
        self.manager.complete_measurement("Valve2", 10.0, 1.5)
        valve = self.valvemanager.get_valve("Valve2")
        self.assertIn(10.0, valve.durations)
        self.assertIn(1.5, valve.amounts)
        self.assertNotIn(10.0, self.manager.get_pending("Valve2"))

    def test_build_testset(self):
        self.manager.add_pending("Valve1", 10)
        self.manager.add_pending("Valve1", 5)
        self.manager.add_pending("Valve2", 20)
        self.assertEqual(self.manager.build_test_set(), {"Valve1": 10, "Valve2": 20})

    def test_build_statemachine(self):
        self.manager.add_pending("Valve1", 10)
        self.manager.add_pending("Valve2", 15)
        statemachine, test_set = self.manager.build_statemachine()
        self.assertIsInstance(statemachine, StateMachine)
