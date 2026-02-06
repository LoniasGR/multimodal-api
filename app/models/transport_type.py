from enum import StrEnum


class TransportType(StrEnum):
    FOOT = "FOOT"
    SCOOTER = "SCOOTER"
    CAR = "CAR"
    BUS = "BUS"
    SEA_VESSEL = "SEA_VESSEL"

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
        if not isinstance(other, TransportType):
            return False
        return self.name == other.name
