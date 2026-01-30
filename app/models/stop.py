from sqlmodel import SQLModel, Field
from .location import Location
from .stop_type import StopType


class StopBase(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    type: StopType


class StopDB(StopBase, table=True):
    lat: float
    lng: float


class Stop(StopBase):
    loc: Location

    def __post_init__(self) -> None:
        # Why: fail fast with clear messages on type/value errors.
        if not isinstance(self.id, int):
            raise TypeError("id must be int")
        if not isinstance(self.name, str):
            raise TypeError("name must be str")
        if self.name.strip() == "":
            raise ValueError("name must be non-empty")
        if not isinstance(self.type, StopType):
            raise TypeError("type must be VehicleStopType")
        if not isinstance(self.loc, Location):
            raise TypeError("loc must be a Location instance")

    def uid(self) -> str:
        return f"{self.type.abbr()}-{self.id}"

    def set_loc(self, new_loc: Location) -> None:
        self.loc = new_loc

    def __str__(self) -> str:
        return f"Stop(id={self.id}, name={self.name}, type={self.type}, loc={self.loc})"

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Stop):
            return False
        return self.uid() == other.uid()

    # EXTEND IT WITH VEHICLE LINES AND TIMETABLES
