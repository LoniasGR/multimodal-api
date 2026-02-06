from sqlmodel import SQLModel, Field
from .location import Location
from .stop_type import StopType


class StopBase(SQLModel):
    name: str = Field(unique=True, index=True)
    type: StopType


class Stop(StopBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    latitude: float | None = Field(default=None, exclude=True)
    longitude: float | None = Field(default=None, exclude=True)


class StopCreate(StopBase):
    location: Location


class StopPublic(StopCreate):
    id: int
