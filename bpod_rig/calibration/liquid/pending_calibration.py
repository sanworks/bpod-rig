import logging

import bpod_core.bpod
from pydantic import Field
from bpod_core.fsm import StateMachine

from bpod_rig.calibration.liquid.models import ValveDataManager, ValveData

logger = logging.getLogger(__name__)


class PendingValve(ValveData):
    pending_durations: list[float] = Field(
        default=[],
        description="List of durations that are pending calibration measurements.",
    )

    valve_controller: str = Field(
        default="unknown",
        description="The controlling hardware of the valve "
                    "(e.g., 'StateMachine', 'PortArray').",
    )

    def __init__(self, **data):
        super().__init__(**data)
        if self.name.startswith("PA"):
            self.valve_controller = "PortArray"
        elif self.name.startswith("Valve"):
            self.valve_controller = "StateMachine"
        else:
            raise ValueError("Valve name not recognised for controller assignment.")

    def action(self, actiontype: str) -> dict[str, str | list[str | int] | bool]:
        """Define the output action for this valve

        Parameters
        ----------
        actiontype : str
            What kind of action the valve is performing: "open" or "close"

        Returns
        -------
        dict
            Action definition for valve that can be fed to
            StateMachine.add_state(**, output_actions=)
        """
        if actiontype not in ["open", "close"]:
            raise ValueError("Action type not recognised.")
        if self.valve_controller == "StateMachine":
            if actiontype == "open":
                # matlab code
                # ValvePhysicalAddress = 2.^(0:7);
                # ValveAddress = ValvePhysicalAddress(valveID)
                # valve_id = int(self.name[5:])
                # valve_address = 2 ** (valve_id - 1)
                # return {'ValveState': valve_address}
                return {self.name: True}

            if actiontype == "close":
                raise ValueError("StateMachine valves do not have a close action.")
            raise ValueError("Action type not recognised.")
        if self.valve_controller == "PortArray":
            target_module = self.name[0:3]
            portnumber = self.name[4]
            if actiontype == "open":
                # TODO: serial message byte parsing hasn't been checked
                action_serial = ["V", portnumber, 1]
                return {target_module: action_serial}
            if actiontype == "close":
                action_serial = ["V", portnumber, 0]
                return {target_module: action_serial}
            raise ValueError("Action type not recognised")
        raise ValueError("Valve controller not recognised.")

    @property
    def is_pending(self) -> bool:
        return len(self.pending_durations) > 0


class PendingMeasurementsManager:
    """Manage valves and their pending values.

    Maintains list of pending valves (which store pending values), and can construct a
    state machine to test the pending durations.
    """

    _valvemanager: ValveDataManager
    """The real data used by Bpod."""
    valves: list[PendingValve]
    """All of the pending valves that are being managed"""
    n_pulses: int = 100
    """number of pulses to delivery across the test"""
    pulse_interval: float = 0.2
    """time (s) between two different valves pulsing"""
    pulse_set_pause: float = 0.5
    """time (s) between each set of pulses"""

    def __init__(self, valvemanager: ValveDataManager):
        self._valvemanager = valvemanager
        self.valves = [
            PendingValve(ValveName=valve.name) for valve in valvemanager.valve_datas
        ]

    def get_valve(self, valvename: str) -> PendingValve:
        """Retrieve object for a pending valve."""
        if valvename not in self._valvemanager.valve_names:
            raise KeyError(f"Valvename '{valvename}' not found in manager.")
        return next(valve for valve in self.valves if valve.name == valvename)

    def get_pending(self, valvename: str) -> list[float]:
        """Return pending durations from a given valve."""
        return self.get_valve(valvename).pending_durations

    def add_pending(self, valvename: str, duration: float) -> None:
        """Add a pending duration to the valve's list."""
        if duration in self.get_pending(valvename):
            raise ValueError("Duration already pending.")
        if duration in self._valvemanager.get_valve(valvename).durations:
            raise ValueError("Duration already exists in valve calibration.")

        self.get_pending(valvename).append(duration)

    def remove_pending(self, valvename: str, duration: float) -> None:
        """Remove a pending duration from the valve's pending record."""
        if duration not in self.get_pending(valvename):
            raise ValueError("Duration for completed measurement is not pending.")

        self.get_pending(valvename).remove(duration)

    def complete_measurement(
        self, valvename: str, duration: float, amount: float
    ) -> None:
        """Record an amount dispensed for a duration that was measured.

        Remove duration from pending list and adds completed measurement to the valve
        manager.

        Parameters
        ----------
        valvename : str
            Name of the valve that has been tested and weighed.
        duration : float
            Duration (ms) of valve opening
        amount : float
            Quantity (mg or mL) released from the duration.
        """
        if duration not in self.get_pending(valvename):
            raise ValueError("Duration not found in existing pending values.")
        self.remove_pending(valvename, duration)
        self._valvemanager.get_valve(valvename).add_measurement(duration, amount)
        logger.debug("Completed measurement for %s %s ms", valvename, duration)

    def build_test_set(self) -> dict[str, float]:
        """Create dict of valves and the duration (ms) to test.

        Will take the first (oldest) duration in the valve's pending values.
        """
        pending_valves = [valve for valve in self.valves if valve.is_pending]
        test_set = {}
        for valve in pending_valves:
            test_set[valve.name] = valve.pending_durations[0]
        return test_set

    def build_statemachine(
        self, test_set: dict | None = None
    ) -> tuple[StateMachine, dict[str, float]]:
        """Build the state machine to test all pending valves.

        The state machine is constructed using object parameters:
        - n_pulses: number of pulses to deliver.
        - pulse_interval: Duration (s) between one valve's pulse end and next's start.
        - pulse_set_pause: Duration (s) between a set of pulses.

        The amount of liquid dispensed from the state machine
        For example, 100 pulses totaling 0.200g (200mg) is 0.200g / 100 = 2mg = 2mL

        Parameters
        ----------
        test_set : dict | None, optional
            Names of valves and durations to build state machine for. If not provided,
            test all valves that have pending durations using their oldest duration.
        Returns
        -------
        tuple[StateMachine, dict[str, float]]
            - The finite state machine.
            - dict of which valves and what duration the state machine was built for.
        """
        fsm = StateMachine()
        if test_set is None:
            test_set = self.build_test_set()
        valve_names = list(test_set.keys())
        logger.debug("Building test set for %s", valve_names)
        pending_valves = [valve for valve in self.valves if valve.is_pending]
        n_pending = len(pending_valves)
        if n_pending == 0:
            raise AssertionError("No pending valves found.")
        for x, valve_name in enumerate(valve_names):
            pending_valve = self.get_valve(valve_name)
            duration = test_set[valve_name]
            if x < n_pending - 1:
                next_valve = self.get_valve(valve_names[x + 1])
            else:
                next_valve = self.pulse_set_pause
            add_valve_states(
                fsm, pending_valve, duration, next_valve, self.pulse_interval
            )
        return fsm, test_set


def add_valve_states(
    fsm: StateMachine,
    pending_valve: PendingValve,
    duration: float,
    next_valve: PendingValve | float,
    interval_delay_duration: float,
):
    """Add the pending valve to a state machine.

    Parameters
    ----------
    fsm : StateMachine
        Existing state machine to add states for the valve to.
    pending_valve : PendingValve
        Valve to create states to use for calibration
    duration : float
        Duration (ms) of valve open.
    next_valve : PendingValve | float
        The next valve object in the cycle, or the float for the pause duration (s)
        between pulse sets.
    interval_delay_duration : float
    """
    last_valve = isinstance(next_valve, float)
    if last_valve:
        pulse_set_pause_duration = next_valve
        next_state = "PulseSetPause"
    else:
        if not isinstance(next_valve, PendingValve):
            raise ValueError("Next valve must be a PendingValve or float.")
        pulse_set_pause_duration = None
        next_state = f"Pulse{next_valve.name}"

    # Add valve openings to the state machine
    if pending_valve.valve_controller == "StateMachine":
        # Valve is wired i.e. open while state is active
        fsm.add_state(
            name=f"Pulse{pending_valve.name}",
            timer=duration / 1000,
            transitions={"Tup": f"Delay{pending_valve.name}"},
            actions=pending_valve.action("open"),
            comment="Open valve for duration of state, with closure at the end.",
        )
    elif pending_valve.valve_controller == "PortArray":
        # Valve is controlled by serial messaging i.e. discrete open/close messages
        fsm.add_state(
            name=f"Pulse{pending_valve.name}",
            timer=duration / 1000,
            transitions={"Tup": f"EndPulse{pending_valve.name}"},
            actions=pending_valve.action("open"),
            comment="Send message to Port Array Module to open the valve.",
        )
        fsm.add_state(
            name=f"EndPulse{pending_valve.name}",
            timer=0,
            transitions={"Tup": f"Delay{pending_valve.name}"},
            actions=pending_valve.action("close"),
            comment="Send message to Port Array module to close the valve.",
        )
    else:
        raise ValueError("Valve controller not recognised.")

    fsm.add_state(
        name=f"Delay{pending_valve.name}",
        timer=interval_delay_duration,
        transitions={"Tup": next_state},
        actions={},
        comment="Pause before opening the next valve.",
    )

    if last_valve:
        # If last valve in set, enter this state following the valve's Delay.
        fsm.add_state(
            name="PulseSetPause",
            timer=pulse_set_pause_duration,
            transitions={"Tup": "exit"},
            actions={},
            comment="Pause when the entire set of valves is completed.",
        )


def run_calibration(
    bpodsystem: bpod_core.bpod.Bpod,
    pending_manager: PendingMeasurementsManager,
    verbose: bool = False,
) -> dict[str, float]:
    """Run a calibration sequence using Bpod state machine.

    Parameters
    ----------
    bpodsystem : bpod_core.bpod.Bpod
        Active Bpod machine.
    pending_manager : PendingMeasurementsManager
        Object storing valve data
    verbose : bool, optional
        Print progress, default False.

    Returns
    -------
    dict[str, float]
        Dictionary of valve names and the duration (ms) of the pulse added to the
        state machine.
    """

    # Build the state machine
    fsm, test_set = pending_manager.build_statemachine()
    if verbose:
        print("Running liquid calibration:")
        print(f"\t{pending_manager.n_pulses} pulses.")
        print(f"\t{pending_manager.pulse_interval} between each pulse.")
        print(f"\t{pending_manager.pulse_set_pause} between each pulse set.")
        for valvename in test_set:
            print(f"- {valvename}: duration {test_set[valvename]} ms")

    bpodsystem.send_state_machine(fsm)
    logger.debug("Running calibration state machine.")
    # Run the state machine
    for _ in range(pending_manager.n_pulses):
        bpodsystem.run_state_machine()

    return test_set
