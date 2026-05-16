from typing import Callable
from types import MethodType

from bpod_core.bpod import Bpod, RemoteBpod
from bpod_rig.session.bpod_session import BpodSession


class BpodProtocol:
    name: str = None
    version: str = "0"
    default_config: dict = dict()

    def __init__(self, bpod_session: BpodSession, protocol_function: Callable | None = None):
        self.session: BpodSession = bpod_session
        self.end_session: bool = False

        self.protocol_name: str | None = None
        self.protocol_version: str | None = None

        self._protocol_function: Callable | None = protocol_function

        if self._protocol_function:
            # If the user writes a "simple" protocol.py, a handle to the function
            # can be passed to BpodProtocol to override the self.protocol function
            self.protocol = MethodType(self._protocol_function, self.session)

    def setup(self):
        pass

    def protocol(self):
        raise NotImplementedError("You must implement your Bpod protocol within the run function!")

    def teardown(self):
        pass

    def run(self):
        self.setup()
        self.protocol()
        self.teardown()

    @property
    def bpod(self) -> Bpod | RemoteBpod:
        if self.session.bpod is None:
            raise AttributeError("Your session does not have an active Bpod connection!")
        return self.session.bpod
