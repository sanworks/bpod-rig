import random

from bpod_core.bpod import Bpod
from bpod_core.fsm import StateMachine


def example_light_2afc_protocol(bpod: Bpod, *args, **kwargs) -> None:
    """
    Light-based 2-alternative forced choice (2AFC) protocol.

    A simple 2AFC task where the mouse pokes in a center port to initiate a trial.
    After a variable delay, lights illuminate indicating left or right choices.
    Correct choices lead to reward, incorrect choices to timeout.
    """
    # Define parameters
    # TODO: implement settings loadings
    # TODO: implement settings GUI
    # If settings file was empty, populate with default settings
    reward_amount = 3  # ul
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
        # left_valve_time, right_valve_time = bpod.get_valve_times(reward_amount, [1, 3])
        left_valve_time, right_valve_time = 0.1, 0.1  # Placeholder valve times

        # Determine trial-specific state machine variables
        if trial_types[current_trial] == 1:
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
            transitions={"Port2In": "CueDelay"},
            actions=None,
        )

        sma.add_state(
            name="CueDelay",
            timer=cue_delay,
            transitions={
                "Port2Out": "WaitForPoke",
                "Tup": "WaitForPortOut",
            },
            actions=None,
        )

        sma.add_state(
            name="WaitForPortOut",
            timer=0,
            transitions={"Port2Out": "WaitForResponse"},
            actions=stimulus_output,
        )

        sma.add_state(
            name="WaitForResponse",
            timer=response_time,
            transitions={
                "Port1In": left_poke_action,
                "Port3In": right_poke_action,
                "Tup": "exit",
            },
            actions=stimulus_output,
        )

        sma.add_state(
            name="LeftRewardDelay",
            timer=reward_delay,
            transitions={
                "Tup": "LeftReward",
                "Port1Out": "CorrectEarlyWithdrawal",
            },
            actions=None,
        )

        sma.add_state(
            name="RightRewardDelay",
            timer=reward_delay,
            transitions={
                "Tup": "RightReward",
                "Port3Out": "CorrectEarlyWithdrawal",
            },
            actions=None,
        )

        sma.add_state(
            name="LeftReward",
            timer=left_valve_time,
            transitions={"Tup": "Drinking"},
            actions={"ValveState": 1},
        )

        sma.add_state(
            name="RightReward",
            timer=right_valve_time,
            transitions={"Tup": "Drinking"},
            actions={"ValveState": 4},
        )

        sma.add_state(
            name="Drinking",
            timer=0,
            transitions={
                "Port1Out": "DrinkingGrace",
                "Port3Out": "DrinkingGrace",
            },
            actions=None,
        )

        sma.add_state(
            name="DrinkingGrace",
            timer=0.5,
            transitions={
                "Tup": "exit",
                "Port1In": "Drinking",
                "Port3In": "Drinking",
            },
            actions=None,
        )

        sma.add_state(
            name="PunishTimeout",
            timer=punish_timeout,
            transitions={"Tup": "exit"},
            actions=None,
        )

        sma.add_state(
            name="CorrectEarlyWithdrawal",
            timer=0,
            transitions={"Tup": "exit"},
            actions=None,
        )

        # Send description to the Bpod State Machine device
        bpod.send_state_machine(sma)

        # Run the trial
        bpod.run_state_machine()

        # TODO: post run updates and data handling
