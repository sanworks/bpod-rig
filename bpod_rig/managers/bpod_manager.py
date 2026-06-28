from typing import TYPE_CHECKING, TypeAlias

from bpod_core.bpod import discover_bpod
from bpod_core.bpod.structs import BpodInfo

from bpod_rig import log

if TYPE_CHECKING:
    from bpod_rig.log import BpodLogger


SerialNumber: TypeAlias = str


class BpodManager:
    def __init__(self) -> None:
        self.logger: BpodLogger = log.get_logger(self.__class__.__name__)
        self._all_local_bpods: dict[SerialNumber, BpodInfo] | None = None
        # self.remote_bpods: dict[SerialNumber, BpodInfo] | None = None

        self.current_bpod: BpodInfo | None = None
        self.refresh()

    def refresh(self) -> None:
        self._get_local_bpods()

    def select_bpod(
        self, serial: SerialNumber | None = None, index: int | None = None
    ) -> BpodInfo:
        """Returns a BpodInfo instance requested by the user.

        If there is only one Bpod found, no identifiers are required.

        If there are multiple Bpods, an identifier is required. If an identifier is not
        provided when required, an error will be raised.

        If identifiers are provided, they must exist or an error will be raised. If
        both a serial number and index are provided, the serial will always take
        precedence.

        Parameters
        ----------
        serial : SerialNumber (optional)
            SerialNumber of the Bpod to select
        index : int (optional)
            index of the Bpod to select

        Returns
        -------
            BpodInfo instance

        Raises
        ------
            ValueError
                Raised if no Bpod is found, an identifier is not provided when required,
                or the identifier does not exist


        """
        if self._all_local_bpods is None:
            raise ValueError("No local Bpods found!")

        serials: list[SerialNumber] = list(self._all_local_bpods.keys())

        if serial is not None:
            if serial in serials:
                self.current_bpod = self._all_local_bpods[serial]  # type: ignore
            else:
                raise ValueError(f"Bpod {serial} not found!")
        elif index is not None:
            if 0 > index > len(serials):
                raise IndexError(f"Index {index} out of range!")
            self.current_bpod = self._all_local_bpods[serials[index]]  # type: ignore
        else:
            if len(serials) > 1:
                raise IndexError(f"{len(serials)} Bpods have been found! A serial"
                                 f" number or index is required!")
            self.current_bpod = self._all_local_bpods[serials[0]] # type: ignore

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
