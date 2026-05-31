from typing import Generator

import pytest
from bpod_core.bpod import BpodInfo, discover_bpod

from bpod_rig.managers import BpodManager


def mock_discover_bpod() -> Generator[BpodInfo]:

    bpod_info_1 = BpodInfo(
        serial_number = "abc123",
        port = "COM2",
        name = "Bpod 1"
    )

    bpod_info_2 = BpodInfo(
        serial_number = "xyz456",
        port = "COM3",
        name = "Bpod 2",
    )

    for bpod in [bpod_info_1, bpod_info_2]:
        yield bpod


class TestBpodManager:

    @pytest.fixture(autouse=True)
    def create_bpm(self, request, monkeypatch):
        marker = request.node.get_closest_marker("finds_bpods").args[0]
        print(marker)
        if not marker:
            monkeypatch.setattr("bpod_rig.managers.bpod_manager.discover_bpod", list)
        else:
            monkeypatch.setattr(
                "bpod_rig.managers.bpod_manager.discover_bpod", mock_discover_bpod
                )

        self.bpm = BpodManager()
        self.bpm.load()


    @pytest.mark.finds_bpods(False)
    def test_discover_no_bpods(self, caplog):
        self.bpm.load()
        assert "No local Bpods found!" in caplog.messages
        assert self.bpm._all_local_bpods is None
        assert self.bpm._get_local_bpods() is None

    @pytest.mark.finds_bpods(True)
    def test_discover_bpods(self):
        assert self.bpm._all_local_bpods is not None
        assert list(self.bpm._all_local_bpods.keys()) == ["abc123", "xyz456"]
        assert self.bpm._get_local_bpods() is self.bpm._all_local_bpods

    @pytest.mark.finds_bpods(False)
    def test_select_bpod_no_bpods(self):
        with pytest.raises(ValueError):
            self.bpm.select_bpod()

    @pytest.mark.finds_bpods(True)
    def test_select_bpod(self):

        assert self.bpm._all_local_bpods is not None

        current_bpod = self.bpm.select_bpod()
        assert self.bpm.current_bpod is current_bpod
        assert self.bpm.current_bpod is self.bpm._all_local_bpods["abc123"]
        assert self.bpm.current_bpod is not self.bpm._all_local_bpods["xyz456"]
        assert self.bpm.current_bpod.port == "COM2"
        assert self.bpm.current_bpod.name == "Bpod 1"

        self.bpm.select_bpod(serial = "xyz456")
        assert self.bpm.current_bpod is self.bpm._all_local_bpods["xyz456"]
        assert self.bpm.current_bpod.serial_number == "xyz456"
        assert self.bpm.current_bpod.port == "COM3"
        assert self.bpm.current_bpod.name == "Bpod 2"

        self.bpm.select_bpod(index=1)
        assert self.bpm.current_bpod is self.bpm._all_local_bpods["xyz456"]
        assert self.bpm.current_bpod.serial_number == "xyz456"
        assert self.bpm.current_bpod.port == "COM3"
        assert self.bpm.current_bpod.name == "Bpod 2"

    @pytest.mark.finds_bpods(True)
    def test_select_bpod_errors(self):
        with pytest.raises(KeyError):
            self.bpm.select_bpod(serial="bad_serial")

        with pytest.raises(IndexError):
            self.bpm.select_bpod(index=99)

        with pytest.raises(IndexError):
            self.bpm.select_bpod(index=-99)
