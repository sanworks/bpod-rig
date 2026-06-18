import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from bpod_core.bpod import Bpod

from bpod_rig.config import SystemSettings

if TYPE_CHECKING:
    from bpod_rig.log import BpodLogger


@dataclass
class SystemInfo:
    operating_system: str | None = None


class BpodSystem:
    def __init__(
        self,
        bpod: Bpod,
        system_settings: SystemSettings,
    ) -> None:

        self.logger: BpodLogger = cast("BpodLogger", logging.getLogger(__name__))
        self.bpod: Bpod = bpod
        self.system_settings: SystemSettings = system_settings

        self.protocol: None = None
        self.subject: None = None

    @classmethod
    def create(cls, *args, **kwargs) -> "BpodSystem": #noqa
        return cls(
            *args,
            **kwargs
        )
    # Super Placeholder
