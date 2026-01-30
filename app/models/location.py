import math
from sqlmodel import SQLModel


class Location(SQLModel):
    latitude: float
    longitude: float

    def __composite_values__(self):
        return self.latitude, self.longitude

    def __post_init__(self) -> None:
        # Why: explicit float-only API and finite checks.
        if not isinstance(self.latitude, float) or not isinstance(
            self.longitude, float
        ):
            raise TypeError("lat and lng must be float")
        if not (math.isfinite(self.latitude) and math.isfinite(self.longitude)):
            raise ValueError("lat and lng must be finite numbers")
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError("lat must be in [-90, 90]")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError("lng must be in [-180, 180]")

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

    def distance_to(self, other: "Location") -> float:
        """
        Great-circle distance to another Position in meters (Haversine).
        Raises:
            TypeError: when `other` is not a Position.
        """
        if not isinstance(other, Location):
            raise TypeError("other must be a Position")

        # Convert degrees to radians.
        lat1 = math.radians(self.latitude)
        lng1 = math.radians(self.longitude)
        lat2 = math.radians(other.latitude)
        lng2 = math.radians(other.longitude)

        dlat = lat2 - lat1
        dlng = lng2 - lng1

        # Haversine formula
        sin_dlat = math.sin(dlat / 2.0)
        sin_dlng = math.sin(dlng / 2.0)
        a = sin_dlat * sin_dlat + math.cos(lat1) * math.cos(lat2) * sin_dlng * sin_dlng
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

        R = 6_371_000.0  # mean Earth radius in meters
        return R * c

    def __str__(self) -> str:
        return f"Position(lat={self.latitude}, lng={self.longitude})"

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Location):
            return False
        return self.latitude == other.latitude and self.longitude == other.longitude
