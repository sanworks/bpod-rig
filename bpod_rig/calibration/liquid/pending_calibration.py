from pydantic import Field
from bpod_core.fsm import StateMachine

from bpod_rig.calibration.liquid.models import ValveDataManagerClass, ValveDataClass


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
        elif self.name.startswith("Valve"):
            self.valve_controller = "StateMachine"
        else:
            raise ValueError("Valve name not recognised for controller assignment.")

    def action(self, actiontype: str) -> dict[str, str | list[str | int]]:
        assert actiontype in ["open", "close"]
        if self.valve_controller == "StateMachine":
            valve_id = int(self.name[5:])
            if actiontype == "open":
                # matlab code
                # ValvePhysicalAddress = 2.^(0:7);
                # ValveAddress = ValvePhysicalAddress(valveID)
                valve_address = 2 ** (valve_id - 1)
                return {'ValveState': valve_address}
            elif actiontype == "close":
                raise ValueError("StateMachine valves do not have a close action.")
            else:
                raise ValueError("Action type not recognised.")
        elif self.valve_controller == "PortArray":
            target_module = self.name[0:3]
            portnumber = self.name[4]
            if actiontype == "open":
                # TODO: serial message byte parsing hasn't been checked
                action_serial = ['V', portnumber, 1]
                return {target_module: action_serial}
            elif actiontype == "close":
                action_serial = ['V', portnumber, 0]
                return {target_module: action_serial}
            else:
                raise ValueError("Action type not recognised")
        else:
            raise ValueError("Valve controller not recognised.")

    @property
    def is_pending(self) -> bool:
        return len(self.pending_durations) > 0


class PendingMeasurementsManager:
    _valvemanager: ValveDataManagerClass
    valves: list[PendingValve]

    def __init__(self, valvemanager: ValveDataManagerClass):
        self._valvemanager = valvemanager
        self.valves = [
            PendingValve(ValveName=valve.name) for valve in valvemanager.valve_datas
        ]

    def get_pending(self, valvename: str) -> list[float]:
        if valvename not in self._valvemanager.valve_names:
            raise KeyError(f"Valvename '{valvename}' not found in manager.")

        return next(
            valve for valve in self.valves if valve.name == valvename
        ).pending_durations

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

    def complete_measurement(
        self, valvename: str, duration: float, amount: float
    ) -> None:
        assert duration in self.get_pending(valvename)
        self.remove_pending(valvename, duration)
        self._valvemanager.get_valve(valvename).add_measurement(duration, amount)


def add_valve_states(
    fsm: StateMachine, pending_valve: PendingValve, next_valve: PendingValve | float,
    delay_duration: float
) -> tuple[str, float]:
    """Add the pending valve to a state machine.

    Parameters
    ----------
    fsm : StateMachine
        Existing state machine to add states for the valve to.
    pending_valve : PendingValve
        Valve to create states to use for calibration
    next_valve : PendingValve | float
        The next valve object in the cycle, or the float for the pause duration (s) between pulse sets.
    delay_duration : float

    Returns
    -------
    tuple[str, float]
        Valve name and the duration (ms) of the pulse added to the state machine.
    """
    assert len(pending_valve.durations) > 0
    duration = pending_valve.pending_durations[0]
    last_valve = isinstance(next_valve, float)
    if last_valve:
        pulse_set_pause_duration = next_valve
        next_state = 'PulseSetPause'
    else:
        assert (isinstance(next_valve, PendingValve))
        pulse_set_pause_duration = None
        next_state = f"Pulse{next_valve.name}"

    # Add valve openings to the state machine
    if pending_valve.valve_controller == 'StateMachine':
        # Valve is wired i.e. open while state is active
        fsm.add_state(
            name=f"Pulse{pending_valve.name}",
            timer=duration / 1000,
            state_change_conditions={'Tup': f"Delay{pending_valve.name}"},
            output_actions={'Valve1'}
        )
    elif pending_valve.valve_controller == 'PortArray':
        # Valve is controlled by serial messaging i.e. discrete open/close messages
        fsm.add_state(
            name=f"Pulse{pending_valve.name}",
            timer=duration / 1000,
            state_change_conditions={'Tup': f"EndPulse{pending_valve.name}"},
            output_actins={}
        )
        fsm.add_state(
            name=f"EndPulse{pending_valve.name}",
            timer=0,
            state_change_conditions={'Tup': f"Delay{pending_valve.name}"},
            output_actions={}
        )
    else:
        raise ValueError("Valve controller not recognised.")

    fsm.add_state(
        name=f"Delay{pending_valve.name}",
        timer=delay_duration,
        state_change_conditions={'Tup', next_state},
        output_actions={}
    )

    if last_valve:
        fsm.add_state(
            name="PulseSetPause",
            timer=pulse_set_pause_duration,
            state_change_conditions={'Tup': 'exit'},
            output_actions={}
        )
    return pending_valve.name, duration


def run_calibration(
    pending_manager: PendingMeasurementsManager,
    n_pulses: int,
    pulse_interval: float = 0.2,
    pulse_set_pause: float = 0.5,
    verbose: bool = True,
) -> dict[str, float]:
    """Run a calibration sequence using Bpod state machine.

    Parameters
    ----------
    pending_manager : PendingMeasurementsManager
        Object storing valve data
    n_pulses : int
        Number of pulses to deliver for all valves.
    pulse_interval : float, optional
        Time (s) between each pulse of each valve.
    pulse_set_pause : float, optional
        Time (s) between a round (after all valves pulsed)
    verbose : bool, optional
        Print progress.

    Returns
    -------
    dict[str, float]
        Dictionary of valve names and the duration (ms) of the pulse added to the state machine.
    """

    # Build the state machine
    fsm = StateMachine()
    pending_valves = [valve for valve in pending_manager.valves if valve.is_pending]
    n_pending = len(pending_valves)
    if n_pending == 0:
        raise AssertionError("No pending valves found.")
    test_set = {}
    for x, pending_valve in enumerate(pending_valves):
        if x < n_pending - 1:
            next_valve = pending_valves[x + 1]
        else:
            next_valve = pulse_set_pause
        name, duration = add_valve_states(
            fsm, pending_valve, next_valve, pulse_interval
            )
        test_set[name] = duration

    # Run the state machine
    for trial in range(n_pulses):
        pass

    return test_set
