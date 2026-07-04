import time
from pathlib import Path

import pytest

from bpod_rig.protocols import session

pause_time = 0.1  # seconds


def prepare_protocol(parent_folder: Path, protocol_text: str | None = None) -> Path:

    if protocol_text is None:
        protocol_text = r"""
from bpod_rig import get_session
bpod_session = get_session()
print(f"bpod_session.session_folder: {bpod_session.session_folder}")
test_file_path = bpod_session.session_folder / "test_file.txt"
with open(test_file_path, "w") as f:
    f.write("This is a test file.")
"""

    protocol_path = parent_folder / "test_protocol.py"
    protocol_path.write_text(protocol_text)
    return protocol_path


def test_start_protocol_process(tmp_path: Path) -> None:
    protocol_path = prepare_protocol(tmp_path)
    session_folder = tmp_path / "session"
    session_folder.mkdir()

    ipc_handles = {}  # Placeholder for IPC handles

    session.start_protocol_process(
        session_folder=session_folder,
        protocol_path=protocol_path,
        ipc_handles=ipc_handles,
        debug=False,
    )
    session_file = session_folder / "test_file.txt"

    time.sleep(pause_time)
    assert session_file.exists()
