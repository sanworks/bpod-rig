from bpod_core.bpod import Bpod, RemoteBpod
from bpod_rig.session.bpod_session import BpodSession


class BpodProtocol:
    name: str = None
    version: str = "0"
    default_config: dict = dict()

    def __init__(self, bpod_session: BpodSession):
        self.session: BpodSession = bpod_session
        self.end_session: bool = False

        self.protocol_name: str | None = None
        self.protocol_version: str | None = None


    def setup(self):
        pass

    def run(self):
        raise NotImplementedError("You must implement your Bpod protocol within the run function!")

    def teardown(self):
        pass

    @property
    def bpod(self) -> Bpod | RemoteBpod:
        if self.session.bpod is None:
            raise AttributeError("Your session does not have an active Bpod connection!")
        return self.session.bpod
