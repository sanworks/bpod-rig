import logging
from typing import TYPE_CHECKING, TypeAlias, cast

from bpod_core.bpod import BpodInfo, discover_bpod

if TYPE_CHECKING:
    from bpod_rig.log import BpodLogger


SerialNumber: TypeAlias = str


class BpodManager:
    def __init__(self) -> None:
        self.logger: BpodLogger = cast("BpodLogger", logging.getLogger(__name__))
        self._all_local_bpods: dict[SerialNumber, BpodInfo] | None = None
        # self.remote_bpods: dict[SerialNumber, BpodInfo] | None = None

        self.current_bpod: BpodInfo | None = None
        self.refresh()

    def refresh(self) -> None:
        self._get_local_bpods()

    def select_bpod(
        self, serial: SerialNumber | None = None, index: int = 0
    ) -> BpodInfo:
        """Returns a BpodInfo instance.

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
            if serial in serials:
                self.current_bpod = self._all_local_bpods[serial]  # type: ignore
            else:
                raise KeyError(f"Bpod {serial} not found!")
        else:
            if index > len(serials) or index < 0:
                raise IndexError(f"Index {index} out of range!")
            self.current_bpod = self._all_local_bpods[serials[index]]  # type: ignore

        return self.current_bpod

    def _format_all_bpods_info(self) -> str:
        if self._all_local_bpods is None:
            return "No local Bpods found to list!"

        info = [
            f"[{i}]: Local Bpod\n"
            f"Name: {info.name} | Serial Number: {sn}\n"
            f"Port: {info.port} | Location: {info.location}\n\n"
            for i, (sn, info) in enumerate(self._all_local_bpods.items())
        ]

        return f"The following Bpods are available:\n {info}"

    def _get_local_bpods(self) -> dict[SerialNumber, BpodInfo] | None:
        local_bpods = list(discover_bpod())
        # remote_bpods = discover_remote_bpod()

        if len(local_bpods) == 0:
            self._all_local_bpods = None
            self.logger.warning("No local Bpods found!")
            return None

        self._all_local_bpods = {info.serial_number: info for info in local_bpods}
        # self.remote_bpods = {
        #     info.serial_number: info
        #     for info in remote_bpods
        # }

        return self._all_local_bpods

    @property
    def bpod(self) -> BpodInfo | None:
        return self.current_bpod

    def __str__(self) -> str:
        return self._format_all_bpods_info()
