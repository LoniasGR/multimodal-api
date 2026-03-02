from sqlmodel import SQLModel
from .location import Location


class Point(SQLModel):
    name: str
    type: str = "POINT"
    location: Location
