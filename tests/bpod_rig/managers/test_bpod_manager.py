from collections.abc import Generator

import pytest
from bpod_core.bpod.structs import BpodInfo

from bpod_rig.managers import BpodManager

bpod_info_1 = BpodInfo(
    serial_number="serial123",
    port="COM2",
    name="Bpod 1"
)

bpod_info_2 = BpodInfo(
    serial_number="serial456",
    port="COM3",
    name="Bpod 2",
)


def mock_discover_bpod(num_bpods: int = 2) -> Generator[BpodInfo]:
    if num_bpods > 2:
        raise IndexError("Too many Bpods requested!")

    yield from [bpod_info_1, bpod_info_2][:num_bpods]


def compare_bpod_info(selected_bpod: BpodInfo, expected_bpod: BpodInfo) -> None:
    assert selected_bpod.serial_number == expected_bpod.serial_number
    assert selected_bpod.name == expected_bpod.name
    assert selected_bpod.port == expected_bpod.port
    assert selected_bpod is expected_bpod


class TestBpodManager:
    @pytest.fixture(autouse=True)
    def create_bpm(
        self, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        marker = request.node.get_closest_marker("finds_bpods")
        if not marker:
            monkeypatch.setattr("bpod_rig.managers.bpod_manager.discover_bpod", list)
        else:
            num_bpods = marker.args[0]
            monkeypatch.setattr(
                "bpod_rig.managers.bpod_manager.discover_bpod",
                lambda: mock_discover_bpod(num_bpods),
            )

        self.bpm = BpodManager()
        self.bpm.refresh()

    def test_discover_no_bpods(self, caplog: pytest.LogCaptureFixture) -> None:
        self.bpm.refresh()
        assert "No local Bpods found!" in caplog.messages
        assert self.bpm._all_local_bpods is None
        assert self.bpm._get_local_bpods() is None

    @pytest.mark.finds_bpods(2)
    def test_discover_bpods(self) -> None:
        assert self.bpm._all_local_bpods is not None
        assert list(self.bpm._all_local_bpods.keys()) == ["serial123", "serial456"]
        # Is the value returned correctly?
        assert self.bpm._get_local_bpods() is self.bpm._all_local_bpods

    def test_select_bpod_no_bpods(self) -> None:
        with pytest.raises(ValueError):
            self.bpm.select_bpod()

    @pytest.mark.finds_bpods(1)
    def test_select_one_bpod(self) -> None:

        # Test No Parameters
        returned_bpod = self.bpm.select_bpod()
        assert self.bpm.current_bpod is not None
        compare_bpod_info(self.bpm.current_bpod, bpod_info_1)
        compare_bpod_info(returned_bpod, bpod_info_1)

        # Reset current bpod and test select by index
        self.bpm.current_bpod = None
        returned_bpod = self.bpm.select_bpod(index=0)
        assert self.bpm.current_bpod is not None
        compare_bpod_info(self.bpm.current_bpod, bpod_info_1)
        compare_bpod_info(returned_bpod, bpod_info_1)

        # Reset current bpod and test select by serial
        self.bpm.current_bpod = None
        returned_bpod = self.bpm.select_bpod(serial="serial123")
        assert self.bpm.current_bpod is not None
        compare_bpod_info(self.bpm.current_bpod, bpod_info_1)
        compare_bpod_info(returned_bpod, bpod_info_1)

    @pytest.mark.finds_bpods(2)
    def test_select_multiple_bpods(self, caplog: pytest.LogCaptureFixture) -> None:
        returned_bpod = self.bpm.select_bpod(serial="serial123")
        assert self.bpm.current_bpod is not None
        compare_bpod_info(self.bpm.current_bpod, bpod_info_1)
        compare_bpod_info(returned_bpod, bpod_info_1)

        returned_bpod = self.bpm.select_bpod(serial="serial456")
        assert self.bpm.current_bpod is not None
        compare_bpod_info(self.bpm.current_bpod, bpod_info_2)
        compare_bpod_info(returned_bpod, bpod_info_2)

        returned_bpod = self.bpm.select_bpod(index=0)
        assert self.bpm.current_bpod is not None
        compare_bpod_info(self.bpm.current_bpod, bpod_info_1)
        compare_bpod_info(returned_bpod, bpod_info_1)

        returned_bpod = self.bpm.select_bpod(index=1)
        assert self.bpm.current_bpod is not None
        compare_bpod_info(self.bpm.current_bpod, bpod_info_2)
        compare_bpod_info(returned_bpod, bpod_info_2)

    @pytest.mark.finds_bpods(2)
    def test_select_bpod_errors(self, caplog: pytest.LogCaptureFixture) -> None:
        with pytest.raises(ValueError):
            # Parameters are required with multiple Bpods
            self.bpm.select_bpod()
            assert "A serial number or index is required!" in caplog.messages

        with pytest.raises(ValueError):
            self.bpm.select_bpod(serial="bad_serial")
            assert "not found" in caplog.messages

        with pytest.raises(IndexError):
            self.bpm.select_bpod(index=99)
            assert "out of range" in caplog.messages

        with pytest.raises(IndexError):
            self.bpm.select_bpod(index=-99)
            assert "out of range" in caplog.messages

    def test_format_no_bpods(self) -> None:
        string_rep = str(self.bpm)
        assert string_rep == "No local Bpods found to list!"

    @pytest.mark.finds_bpods(1)
    def test_format_one_bpod(self) -> None:
        string_rep = str(self.bpm)
        assert string_rep == (
            "\nThe following Bpods are available:\n"
            "===================================\n"
            "[0]: Local Bpod\n"
            "Name: Bpod 1 | Serial Number: serial123\n"
            "Port: COM2 | Location: \n"
            "\n"
        )

    @pytest.mark.finds_bpods(2)
    def test_format_two_bpods(self) -> None:
        string_rep = str(self.bpm)
        assert string_rep == (
            "\nThe following Bpods are available:\n"
            "===================================\n"
            "[0]: Local Bpod\n"
            "Name: Bpod 1 | Serial Number: serial123\n"
            "Port: COM2 | Location: \n"
            "\n"
            "[1]: Local Bpod\n"
            "Name: Bpod 2 | Serial Number: serial456\n"
            "Port: COM3 | Location: \n"
            "\n"
        )
