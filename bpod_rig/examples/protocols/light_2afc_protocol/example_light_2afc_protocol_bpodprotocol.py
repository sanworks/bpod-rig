import random
from datetime import datetime
from pathlib import Path

from bpod_core.fsm import StateMachine

from bpod_rig.config.system_settings import SystemSettings
from bpod_rig.defaults import DEFAULT_BPOD_PATH
from bpod_rig.protocols import BpodProtocol

settings = SystemSettings.model_validate_json(
    Path(DEFAULT_BPOD_PATH).joinpath("Config/config.json").read_text()
)


def generate_session_folder() -> Path:
    session_time = datetime.now().isoformat(timespec="seconds").replace(":", "-")
    session_name = f"{Path(__file__).stem}_{session_time}"
    session_folder = settings.paths.data_dir / session_name
    session_folder.mkdir(parents=True, exist_ok=False)
    return session_folder

class Light2AFCProtocol(BpodProtocol):
    name = "Light2AFCProtocol_BpodProtocol"
    version = "1"

    def protocol(self):
        """
        Light-based 2-alternative forced choice (2AFC) protocol.

        A simple 2AFC task where the mouse pokes in a center port to initiate a trial.
        After a variable delay, lights illuminate indicating left or right choices.
        Correct choices lead to reward, incorrect choices to timeout.
        """
        session_folder = generate_session_folder()

        # Define parameters
        # TODO: implement settings loadings
        # TODO: implement settings GUI
        # If settings file was empty, populate with default settings
        # reward_amount = 3  # ul
        # How long the mouse must poke in the center to activate the goal port
        cue_delay = 0.2
        # How long until the mouse must make a choice, or forfeit the trial
        response_time = 5
        # How long the mouse must wait in the goal port for reward to be delivered
        reward_delay = 0
        # Timeout duration for incorrect choices
        punish_timeout = 3

        # Define trials
        max_trials = 1000
        trial_types = [random.randint(1, 2) for _ in range(max_trials)]

        # Initialize plots
        # TODO: Implement outcome plots

        # Main loop, runs once per trial
        for current_trial in range(max_trials):
            # Update reward amounts
            left_valve_time, right_valve_time = 0.1, 0.1  # Placeholder valve times

            # Determine trial-specific state machine variables
            if trial_types[current_trial] == 1:
                trial_type = "Left"
            else:
                trial_type = "Right"

            if trial_type == "Left":
                left_poke_action = "LeftRewardDelay"
                right_poke_action = "PunishTimeout"
                stimulus_output = {
                    "PWM1": 255,  # PWM1 controls LED light intensity of port 1 (0-255)
                }
            else:
                left_poke_action = "PunishTimeout"
                right_poke_action = "RightRewardDelay"
                stimulus_output = {
                    "PWM3": 255,  # PWM3 controls LED light intensity of port 3 (0-255)
                }

            # Build new state machine
            sma = StateMachine()

            sma.add_state(
                name="WaitForPoke",
                timer=0,
                transitions={"Port2_High": "CueDelay"},
                actions=None,
            )

            sma.add_state(
                name="CueDelay",
                timer=cue_delay,
                transitions={
                    "Port2_Low": "WaitForPoke",
                    "Tup": "WaitForPort_Low",
                },
                actions=None,
            )

            sma.add_state(
                name="WaitForPort_Low",
                timer=0,
                transitions={"Port2_Low": "WaitForResponse"},
                actions=stimulus_output,
            )

            sma.add_state(
                name="WaitForResponse",
                timer=response_time,
                transitions={
                    "Port1_High": left_poke_action,
                    "Port3_High": right_poke_action,
                    "Tup": ">exit",
                },
                actions=stimulus_output,
            )

            if trial_type == "Left":
                sma.add_state(
                    name="LeftRewardDelay",
                    timer=reward_delay,
                    transitions={
                        "Tup": "LeftReward",
                        "Port1_Low": "CorrectEarlyWithdrawal",
                    },
                    actions=None,
                )
                sma.add_state(
                    name="LeftReward",
                    timer=left_valve_time,
                    transitions={"Tup": "Drinking"},
                    actions={"Valve1": True},
                )
            else:
                sma.add_state(
                    name="RightRewardDelay",
                    timer=reward_delay,
                    transitions={
                        "Tup": "RightReward",
                        "Port3_Low": "CorrectEarlyWithdrawal",
                    },
                    actions=None,
                )

                sma.add_state(
                    name="RightReward",
                    timer=right_valve_time,
                    transitions={"Tup": "Drinking"},
                    actions={"Valve3": True},
                )

            sma.add_state(
                name="Drinking",
                timer=0,
                transitions={
                    "Port1_Low": "DrinkingGrace",
                    "Port3_Low": "DrinkingGrace",
                },
                actions=None,
            )

            sma.add_state(
                name="DrinkingGrace",
                timer=0.5,
                transitions={
                    "Tup": ">exit",
                    "Port1_High": "Drinking",
                    "Port3_High": "Drinking",
                },
                actions=None,
            )

            sma.add_state(
                name="PunishTimeout",
                timer=punish_timeout,
                transitions={"Tup": ">exit"},
                actions=None,
            )

            sma.add_state(
                name="CorrectEarlyWithdrawal",
                timer=0,
                transitions={"Tup": ">exit"},
                actions=None,
            )

            print(f"Starting trial {current_trial}: {trial_type} trial")
            self.bpod.run(sma)

            data = self.bpod.get_data()
            data.write_parquet(session_folder / f"trial_{current_trial}.parquet")
