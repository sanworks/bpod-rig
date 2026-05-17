from __future__ import annotations
from types import MethodType
from typing import Callable, TYPE_CHECKING

from bpod_core.bpod import Bpod, RemoteBpod

if TYPE_CHECKING:
    from bpod_rig.session.bpod_session import BpodSession


class BpodProtocol:
    from bpod_rig.session import BpodSession
    # No circular dependencies here

    name: str = "DefaultProtocol"
    version: str = "0"
    default_config: dict = {}
    def __init__(
        self, bpod_session: BpodSession, protocol_function: Callable | None = None
    ):
        self.session: BpodSession = bpod_session
        self.end_session: bool = False

        self._protocol_function: Callable | None = protocol_function

        if self._protocol_function:
            # If the user writes a "simple" protocol.py, a handle to the function
            # can be passed to BpodProtocol to override the self.protocol function
            self.protocol = MethodType(self._protocol_function, self.session)

    def setup(self):
        pass

    def protocol(self):
        raise NotImplementedError(
            "You must implement your Bpod protocol within the run function!"
        )

    def teardown(self):
        pass

    def run(self):
        self.setup()
        self.protocol()
        self.teardown()

    @property
    def bpod(self) -> Bpod | RemoteBpod:
        if self.session.bpod is None:
            raise AttributeError(
                "Your session does not have an active Bpod connection!"
            )
        return self.session.bpod
