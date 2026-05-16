import datetime

from bpod_rig.session import BpodSession


# TODO: make this a Pydantic model
class BpodSubject:
    def __init__(self):
        self.id: str | None = None
        self.species: str | None = None
        self.DOB: datetime.date | None = None
        self.cohort: str | None = None
        self.genotype: str | None = None
        self.description: str | None = None

        self.current_session: BpodSession | None = None
