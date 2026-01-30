from enum import IntEnum


class StopType(IntEnum):
    SCOOTER_STOP = 1  # Scooter Dock
    CAR_STOP = 2  # Parking Area
    BUS_STOP = 3
    SEA_VESSEL_STOP = 4  # Port

    def abbr(self) -> str:
        if not self.name:
            return ""
        tokens = self.name.split("_")
        # Take the first character of each non-empty token and join them
        acronym = "".join(token[0] for token in tokens if token)
        return acronym

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StopType):
            return False
        return self.name == other.name
