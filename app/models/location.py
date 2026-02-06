import math
from sqlmodel import SQLModel


class Location(SQLModel):
    latitude: float
    longitude: float

    def __composite_values__(self):
        return self.latitude, self.longitude

    def to_tuple(self, reversed=False) -> tuple[float, float]:
        if reversed:
            return (self.longitude, self.latitude)
        return (self.latitude, self.longitude)

    def to_list(self, reversed=False) -> list[float]:
        if reversed:
            return [self.longitude, self.latitude]
        else:
            return [self.latitude, self.longitude]

    @classmethod
    def from_tuple(cls, value: tuple[float, float]) -> "Location":
        """Build from (lat, lng); values are coerced to float."""
        if not isinstance(value, tuple) or len(value) != 2:
            raise TypeError("value must be a (lat, lng) tuple of length 2")
        lat, lng = value
        return cls(latitude=lat, longitude=lng)

    @classmethod
    def from_list(cls, value: list[float], reversed=False):
        if not isinstance(value, list) or len(value) != 2:
            raise TypeError("value must be a list of length 2")
        if reversed:
            lng, lat = value
        else:
            lat, lng = value
        return cls(latitude=lat, longitude=lng)
