from pathlib import Path
from time import sleep

from bpod_rig.protocols import session

pause = 0.2  # seconds


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

    proc = session.start_protocol_process(
        session_folder=session_folder,
        protocol_path=protocol_path,
        ipc_handles=ipc_handles,
        debug=False,
    )

    sleep(pause)
    proc.join()
    assert not proc.is_alive(), "Protocol process did not exit within timeout."
    assert proc.exitcode == 0

    session_file = session_folder / "test_file.txt"
    assert session_file.exists()


def test_pause_and_resume_protocol_process(tmp_path: Path) -> None:
    protocol_text = r"""
from bpod_rig import get_session
bpod_session = get_session()
print(f"bpod_session.session_folder: {bpod_session.session_folder}")
# Simulate a long-running process
for i in range(10):
    bpod_session.handle_pause_condition()
    print(f"Running iteration {i}")
    import time
    time.sleep(.1)
    test_file_path = bpod_session.session_folder / f"test_file_{i}.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test file after pause and resume.")
"""
    protocol_path = prepare_protocol(tmp_path, protocol_text)
    session_folder = tmp_path / "session"
    session_folder.mkdir()
    ipc_handles = session.create_ipc_handles()
    proc = session.start_protocol_process(
        session_folder=session_folder,
        protocol_path=protocol_path,
        ipc_handles=ipc_handles,
        debug=False,
    )
    # proc.start()
    sleep(pause)
    ipc_handles["protocol_run_state"].clear()  # Pause the protocol
    sleep(pause)
    n_files = len(list(session_folder.glob("test_file_*.txt")))
    assert n_files < 10, (
        "Protocol should not have completed all iterations while paused."
    )
    sleep(pause)
    assert len(list(session_folder.glob("test_file_*.txt"))) == n_files, (
        "No new files should be created while paused."
    )
    ipc_handles["protocol_run_state"].set()  # Resume the protocol
    proc.join()
    assert not proc.is_alive(), "Protocol process did not exit within timeout."
    assert len(list(session_folder.glob("test_file_*.txt"))) == 10, (
        "Protocol should have completed all iterations after resuming."
    )
