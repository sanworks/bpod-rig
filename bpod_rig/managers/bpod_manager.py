import logging
import multiprocessing as mp
from multiprocessing.connection import Connection
from pathlib import Path
from typing import cast, Optional, TypeAlias

from bpod_core.bpod import Bpod, BpodInfo, discover_bpod, discover_remote_bpod

from bpod_rig.calibration.liquid.models import ValveDataManager
from bpod_rig.calibration.liquid.pending_calibration import PendingMeasurementsManager
from bpod_rig.log import BpodLogger
from bpod_rig.protocols.runner import load_protocol_function

SerialNumber: TypeAlias = str

class BpodManager:
    def __init__(self, *args, **kwargs) -> None:
        self.logger: BpodLogger = cast(BpodLogger, logging.getLogger(__name__))
        self._all_local_bpods: dict[SerialNumber, BpodInfo] | None = None
        # self.remote_bpods: dict[SerialNumber, BpodInfo] | None = None

        self.last_selected_bpod: BpodInfo | None = None


    def load(self):
        self._get_local_bpods()


    def select_bpod(self, serial: SerialNumber = None, index: int = 0) -> BpodInfo:
        """Returns a BpodInfo instance

        Function will return the BpodInfo instance with the given serial number or
        index. serial will always take precedence over index. If no parameter is
        provided, the first BpodInfo instance will be returned.

        Parameters
        ----------
        serial : SerialNumber (optional)
            SerialNumber of the Bpod to select
        index : int (optional)
            index of the Bpod to select

        Returns
        -------

        BpodInfo instance

        """

        if self._all_local_bpods is None:
            raise ValueError("No local Bpods found!")

        serials: list[SerialNumber] = list(self._all_local_bpods.keys())

        if serial is not None:
            if serial in self._all_local_bpods.keys():
                self.last_selected_bpod = self._all_local_bpods[serial]
            else:
                raise KeyError(f"Bpod {serial} not found!")

        if index > len(serials) or index < 0:
            raise IndexError(f"Index {index} out of range!")

        self.last_selected_bpod = self._all_local_bpods[serials[index]]
        return self.last_selected_bpod


    def _format_all_bpods_info(self):
        if self._all_local_bpods is None:
            return "No local Bpods found to list!"

        info = [
            f"[{i}]: Local Bpod\n"
            f"Name: {info.name} | Serial Number: {sn}\n"
            f"Port: {info.port} | Location: {info.location}\n\n"
            for i, sn, info in enumerate(self._all_local_bpods.items())
        ]

        return f"The following Bpods are available:\n{info}"


    def _get_local_bpods(self):
        local_bpods = discover_bpod()
        # remote_bpods = discover_remote_bpod()

        self._all_local_bpods = {
            info.serial_number: info
            for info in local_bpods
        }
        # self.remote_bpods = {
        #     info.serial_number: info
        #     for info in remote_bpods
        # }

        if self._all_local_bpods is None:
            self.logger.warning("No local Bpods found!")

        return self._all_local_bpods


    @property
    def bpod(self):
        if self.last_selected_bpod is not None:
            return self.last_selected_bpod
        else:
            return None

    def __str__(self):
        return self._format_all_bpods_info()


