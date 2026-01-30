from sqlmodel import SQLModel
from .location import Location


class Point(SQLModel):
    name: str
    type: str = "POINT"
    loc: Location

    def __post_init__(self):
        if not isinstance(self.loc, Location):
            raise TypeError("location must be an instance of Location")

    def uid(self) -> str:
        return self.name

    def __str__(self) -> str:
        return (
            f"Point(name='{self.name}', loc=({self.loc.latitude},{self.loc.longitude}))"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return False
        return self.uid() == other.uid()
