import pytest
from bpod_core.fsm import StateMachine

from bpod_rig.calibration.liquid import pending_calibration, populate_examples, utils


class TestPendingValve:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.pending_valve = pending_calibration.PendingValve(ValveName="Valve3")

    def test_valve_controller_assignment(self):
        valve1 = pending_calibration.PendingValve(ValveName="PA1")
        valve2 = pending_calibration.PendingValve(ValveName="Valve1")
        assert valve1.valve_controller == "PortArray"
        assert valve2.valve_controller == "StateMachine"

    def test_unrecognied_controller_assignment(self):
        with pytest.raises(ValueError):
            pending_calibration.PendingValve(ValveName="HeartValve")

    def test_ispending(self):
        valve = pending_calibration.PendingValve(ValveName="Valve1")
        assert not valve.is_pending
        valve = pending_calibration.PendingValve(ValveName="Valve1")
        valve.pending_durations.append(20)
        assert valve.is_pending


class TestPendingMeasurementsManager:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.valvemanager = utils.create_empty_valve_data_manager()
        populate_examples.add_dummy_measurements(self.valvemanager)
        self.manager = pending_calibration.PendingMeasurementsManager(self.valvemanager)

    def test_get_pending_initial(self):
        assert self.manager.get_pending("Valve1") == []
        assert self.manager.get_pending("Valve2") == []

    def test_get_pending_invalid_valve(self):
        with pytest.raises(KeyError):
            self.manager.get_pending("InvalidValve")

    def test_add_pending(self):
        self.manager.add_pending("Valve1", 10.0)  # valve with values
        assert 10.0 in self.manager.get_pending("Valve1")
        self.manager.add_pending("Valve2", 10.0)  # valve without values
        assert 10.0 in self.manager.get_pending("Valve2")

    def test_add_pending_duplicate(self):
        self.manager.add_pending("Valve1", 10.0)
        with pytest.raises(ValueError):
            self.manager.add_pending("Valve1", 10.0)

    def test_remove_pending(self):
        self.manager.add_pending("Valve1", 10.0)
        self.manager.remove_pending("Valve1", 10.0)
        assert 10.0 not in self.manager.get_pending("Valve1")

    def test_remove_pending_nonexistent(self):
        with pytest.raises(ValueError):
            self.manager.remove_pending("Valve1", 10.0)

    def test_complete_measurement(self):
        self.manager.add_pending("Valve2", 10.0)
        self.manager.complete_measurement("Valve2", 10.0, 1.5)
        valve = self.valvemanager.get_valve("Valve2")
        assert 10.0 in valve.durations
        assert 1.5 in valve.amounts
        assert 10.0 not in self.manager.get_pending("Valve2")

    def test_build_testset(self):
        self.manager.add_pending("Valve1", 10)
        self.manager.add_pending("Valve1", 5)
        self.manager.add_pending("Valve2", 20)
        assert self.manager.build_test_set() == {"Valve1": 10, "Valve2": 20}

    def test_build_statemachine(self):
        self.manager.add_pending("Valve1", 10)
        self.manager.add_pending("Valve2", 15)
        statemachine, test_set = self.manager.build_statemachine()
        assert isinstance(statemachine, StateMachine)
        assert len(test_set.keys()) == 2
        # expect 2 states of open and delay, with final pulse set delay
        n_states = 2 + 2 + 1
        assert len(statemachine.states) == n_states

    # TODO: test build, send, and run of state machine with emulator bpod
