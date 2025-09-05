from calibration.liquid.models import ValveDataManagerClass, ValveDataClass


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
        self.remove_pending(valvename, duration)
        self._valvemanager.get_valve(valvename).add_mesurement(duration, amount)


def run_calibration(
    pending_manager: PendingMeasurementsManager,
    n_pulses: int,
    pulse_interval: float = 0.2,
    pulse_set_pause: float = 0.5,
    verbose: bool = True,
) -> None:
    """Run a calibration sequence using Bpod state machine.

    Parameters
    ----------

    """

    from bpod_core.fsm import StateMachine

    fsm = StateMachine()

    fsm.add_state(
        name="Port1Light",
        timer=1,
        state_change_conditions={"BNC1_High": "Port2Light"},
        output_actions={"PWM1": 255},
    )
    fsm.add_state(
        name="Port2Light",
        timer=1,
        state_change_conditions={"Tup": ">exit"},
        output_actions={"PWM2": 255},
    )


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
        else:
            self.valve_controller = "StateMachine"

    def get_calibration_run_info(self) -> float:
        pass
