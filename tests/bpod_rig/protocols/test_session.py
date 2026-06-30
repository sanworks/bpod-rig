from pathlib import Path

import pytest


def prepare_protocol(tmp_dir: Path) -> Path:

    protocol_text = r"""
from bpod_rig import get_session
bpod_session = get_session()
print(f"bpod_session.session_folder: {bpod_session.session_folder}")
"""


    protocol_path = tmp_dir / "test_protocol.py"
    protocol_path.write_text(protocol_text)
    return protocol_path
