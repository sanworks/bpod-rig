from bpod_core.bpod import Bpod

from bpod_rig.examples.protocols.example_light_2afc_protocol import example_light_2afc_protocol

if __name__ == "__main__":
    with Bpod() as bpod:
        example_light_2afc_protocol(bpod)
    # from unittest.mock import MagicMock
    # bpod = MagicMock(spec=Bpod)
    # bpod.run.side_effect = lambda sma: print(f"Running state machine: {sma}")
