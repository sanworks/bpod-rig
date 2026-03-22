import pytest

from bpod_rig.examples.protocols.example_light_2afc_protocol import example_light_2afc_protocol

def test_protocol():
    # Run the protocol for a short duration to ensure it initializes and runs without errors.
    Bpod = None
    example_light_2afc_protocol(Bpod)