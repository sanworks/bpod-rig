import datetime

import pytest

from bpod_rig.calibration.liquid import utils
from bpod_rig.calibration.liquid.models import ValveData, ValveDataManager
from bpod_rig.calibration.liquid.populate_examples import create_default_json


class TestSuggestDuration:
    @pytest.fixture(autouse=True)
    def setup_method(self) -> None:
        self.valve = ValveData(ValveName="Test Valve")
        self.range_low = 2
        self.range_high = 10
        self.suggest_duration = lambda: utils.suggest_duration(
            self.valve, self.range_low, self.range_high
        )

    def test_no_measures(self) -> None:
        assert self.suggest_duration() == 48

    def test_one_measure(self) -> None:
        self.valve.add_measurement(57, 7.5)
        assert self.suggest_duration() == 36

    def test_two_measures(self) -> None:
        self.valve.add_measurement(22, 2)
        self.valve.add_measurement(66, 9.5)
        assert self.suggest_duration() == pytest.approx(44.0, abs=0.001)


class TestCheckValveManagerUserUpdate:
    @pytest.fixture(autouse=True)
    def setup_method(self) -> None:
        self.manager = ValveDataManager()

    def test_earlier(self) -> None:
        self.manager.metadata.modification_datetime = datetime.datetime(1999, 1, 1)
        assert not utils.check_valvemanager_user_updated(self.manager)

    def test_later(self) -> None:
        self.manager.create_valve("Valve1")
        self.manager.get_valve("Valve1").add_measurement(15, 20)
        assert utils.check_valvemanager_user_updated(self.manager)

    def test_equal(self) -> None:
        self.manager.metadata.modification_datetime = datetime.datetime(2000, 1, 1)
        assert not utils.check_valvemanager_user_updated(self.manager)

    def test_dummy(self) -> None:

        manager = ValveDataManager.model_validate_json(create_default_json())
        assert not utils.check_valvemanager_user_updated(manager)


class TestCheckCOM:
    @pytest.fixture(autouse=True)
    def setup_method(self) -> None:
        self.manager = ValveDataManager()
        self.manager.metadata.COM = "COM3"

    def test_matching(self) -> None:
        assert utils.check_com(self.manager, "COM3") == "yes"

    def test_no_match(self) -> None:
        assert utils.check_com(self.manager, "COM4") == "no"

    def test_unknown(self) -> None:
        self.manager.metadata.COM = ""
        assert utils.check_com(self.manager, "COM3") == "unknown"
