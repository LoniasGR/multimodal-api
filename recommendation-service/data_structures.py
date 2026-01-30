# ----------------------------------------------------------------------------------------
# Data Structures (and relevant Enumerations) for Route Planning purposes
# ----------------------------------------------------------------------------------------

# TODO: Data Structures for Traffic and
# TODO: Data Structures for Environment Conditions (e.g., Low/Medium/High Traffic, Light/Normal/Heavy Rain)

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple
from enum import IntEnum
import math


@dataclass(frozen=True)  # (frozen=True, slots=True)
class Location:
    lat: float
    lng: float

    def __post_init__(self) -> None:
        # Why: explicit float-only API and finite checks.
        if not isinstance(self.lat, float) or not isinstance(self.lng, float):
            raise TypeError("lat and lng must be float")
        if not (math.isfinite(self.lat) and math.isfinite(self.lng)):
            raise ValueError("lat and lng must be finite numbers")
        if not (-90.0 <= self.lat <= 90.0):
            raise ValueError("lat must be in [-90, 90]")
        if not (-180.0 <= self.lng <= 180.0):
            raise ValueError("lng must be in [-180, 180]")

    def to_tuple(self, reversed=False) -> Tuple[float, float]:
        if reversed:
            return (self.lng, self.lat)
        return (self.lat, self.lng)

    def to_list(self, reversed=False) -> list[int]:
        if reversed:
            return [self.lng, self.lat]
        else:
            return [self.lat, self.lng]

    @classmethod
    def from_tuple(cls, value: Tuple[float, float]) -> "Location":
        """Build from (lat, lng); values are coerced to float."""
        if not isinstance(value, tuple) or len(value) != 2:
            raise TypeError("value must be a (lat, lng) tuple of length 2")
        lat, lng = value
        return cls(lat=lat, lng=lng)

    @classmethod
    def from_list(cls, value: list[float], reversed=False):
        if not isinstance(value, list) or len(value) != 2:
            raise TypeError("value must be a list of length 2")
        if reversed:
            lng, lat = value
        else:
            lat, lng = value
        return cls(lat, lng)

    def distance_to(self, other: "Location") -> float:
        """
        Great-circle distance to another Position in meters (Haversine).
        Raises:
            TypeError: when `other` is not a Position.
        """
        if not isinstance(other, Location):
            raise TypeError("other must be a Position")

        # Convert degrees to radians.
        lat1 = math.radians(self.lat)
        lng1 = math.radians(self.lng)
        lat2 = math.radians(other.lat)
        lng2 = math.radians(other.lng)

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
        return f"Location(lat={self.lat}, lng={self.lng})"

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Location):
            return False
        return self.lat == other.lat and self.lng == other.lng


class Point:
    name: str
    type: str
    loc: Location

    def __init__(self, name: str, loc: Location):
        if not isinstance(loc, Location):
            raise TypeError("location must be an instance of Location")
        self.name = name
        self.type = "POINT"
        self.loc = loc

    def uid(self) -> str:
        return self.name

    def __str__(self) -> str:
        return f"Point(name='{self.name}', loc=({self.loc.lat},{self.loc.lat}))"

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return False
        return self.uid() == other.uid()


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


@dataclass  # (slots=True)
class Stop:
    id: int
    name: str
    type: StopType
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


class TransportType(IntEnum):
    """Means of Transport"""

    FOOT = 1
    SCOOTER = 2  # e-scooter
    CAR = 3  # e-car
    BUS = 4
    SEA_VESSEL = 5

    def abbr(self) -> str:
        if not self.name:
            return ""
        tokens = self.name.split("_")
        # Take the first character of each non-empty token and join them
        acronym = "".join(token[0] for token in tokens if token)
        return acronym

    def char(self) -> str:
        tokens = self.name.split("_")
        return tokens[len(tokens) - 1][0]

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TransportType):
            return False
        return self.name == other.name

    def __str__(self) -> str:
        return self.name


@dataclass  # (slots=True)
class Vehicle:
    id: int
    type: TransportType
    loc: Location
    is_available: bool = True  # new field (default: available)

    def __post_init__(self) -> None:
        # Why: fail fast with precise messages.
        if not isinstance(self.id, int):
            raise TypeError("id must be int")
        if not isinstance(self.type, TransportType):
            raise TypeError("vtype must be TransportType")
        if not isinstance(self.loc, Location):
            raise TypeError("vloc must be Position")

    def uid(self) -> str:
        return f"{self.type.abbr()}-{self.id}"

    def make_available(self):
        self.is_available = True

    def make_unavailable(self):
        self.is_available = False

    def set_location(self, new_pos: Location) -> None:
        """Update location."""
        self.loc = new_pos

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vehicle):
            return False
        return self.uid() == other.uid()

    def __str__(self) -> str:
        return (
            f"Vehicle(id={self.id}, "
            f"type={self.type}, "
            f"loc={self.loc}, "
            f"is_available={self.is_available})"
        )


def isPoint(o):
    return isinstance(o, Point)


def isStartPoint(o):
    return isinstance(o, Point) and o.name == "START"


def isEndPoint(o):
    return isinstance(o, Point) and o.name == "END"


def isVehicle(o):
    return isinstance(o, Vehicle)


def isCar(o):
    return isinstance(o, Vehicle) and o.type == TransportType.CAR


def isBus(o):
    return isinstance(o, Vehicle) and o.type == TransportType.BUS


def isScooter(o):
    return isinstance(o, Vehicle) and o.type == TransportType.SCOOTER


def isSeaVessel(o):
    return isinstance(o, Vehicle) and o.type == TransportType.SEA_VESSEL


def isStop(o):
    if o is None:
        return False
    return isinstance(o, Stop)


def isCarStop(o):
    return isinstance(o, Stop) and o.type == StopType.CAR_STOP


def isBusStop(o):
    return isinstance(o, Stop) and o.type == StopType.BUS_STOP


def isScooterStop(o):
    return isinstance(o, Stop) and o.type == StopType.SCOOTER_STOP


def isSeaVesselStop(o):
    return isinstance(o, Stop) and o.type == StopType.SEA_VESSEL_STOP


class WeatherConditions:
    def __init__(self, isRaining: bool, isWindy: bool):
        self.isRaining = isRaining
        self.isWindy = isWindy

    def __str__(self):
        return f"WeatherConditions(isRaining={self.isRaining}, isWindy={self.isWindy})"


class TrafficConditions:
    def __init__(self, highTrafficLocations: list):
        self.highTrafficLocations = highTrafficLocations

    def __str__(self):
        return f"TrafficConditions(highTrafficLocations={self.highTrafficLocations})"


class SexValue(IntEnum):
    MALE = 1
    FEMALE = 2
    OTHER = 3

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SexValue):
            return False
        return self.name == other.name

    def __str__(self) -> str:
        return self.name


class AgeGroupValue(IntEnum):
    CHILD = 1
    ADULT = 2
    SENIOR = 3  # Seniors or Elderly

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AgeGroupValue):
            return False
        return self.name == other.name

    def __str__(self) -> str:
        return self.name


class User:
    id: int
    sex: SexValue
    age_group: AgeGroupValue
    loc: Location | None
    is_available: bool = True  # new field (default: available)

    def __init__(
        self,
        id: int,
        sex: SexValue,
        age_group: AgeGroupValue,
        loc: Location | None = None,
    ):
        self.id = id
        self.sex = sex
        self.age_group = age_group
        self.loc = loc

    def uid(self) -> str:
        return "U-" + self.id

    def __repr__(self) -> str:
        return self.__str__()

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def to_str(self) -> str:
        return f"User(id={self.id}, age_group={self.age_group},  is_available={self.is_available})"

    def __str__(self) -> str:
        return (
            f"User(id={self.id}, "
            f"sex={self.sex}, "
            f"age_group={self.age_group}, "
            f"loc={self.loc}, "
            f"is_available={self.is_available})"
        )


# We can possibly add is_holiday ...
# However additioal libraries are necessary for automatically detecting ...


@dataclass
class TempData:
    day_of_week: int  # Monday = 0, Sunday = 6
    hour_of_day: int  # 0–23

    def __init__(self, day_of_week: int, hour_of_day: int):
        self.day_of_week = day_of_week
        self.hour_of_day = hour_of_day

    @classmethod
    def from_datetime(cls, dt: datetime) -> "TempData":
        return cls(day_of_week=dt.weekday(), hour_of_day=dt.hour)

    def __str__(self) -> str:
        return (
            f"TempData(day_of_week={self.day_of_week}, hour_of_day={self.hour_of_day})"
        )


# ----------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Location (and distance)
    print("\nLocation (and distance):")
    athens = Location(37.983810, 23.727539)  # Position(lat=38.0, lng=23.0)
    print("Location of Athens:", athens)
    rome = Location(41.902782, 12.496366)
    print("Location of Rome:", rome)
    print("Athens-Rome 'Straight Line' distance(m):", athens.distance_to(rome))

    # Point
    print("\nPoint:")
    loc_home = Location(37.9838, 23.7275)  # Athens
    home = Point("Home", loc_home)
    print("Point:", home)

    # Stop and Stop Types
    print("\nStop and Stop Types:")
    for mode in StopType:
        print(f"{mode!s} = {int(mode)}")

    center = Location(lat=37.9838, lng=23.7275)
    s = Stop(id=1, name="Syntagma", type=StopType.BUS_STOP, loc=center)
    print("Stop", s)

    # Vehicle and Modes of Transport
    print("\nVehicle and Modes of Transport")
    for mode in TransportType:
        print(f"{mode!s} = {int(mode)}")

    home = Location(lat=37.9755, lng=23.7348)
    v = Vehicle(id=1, type=TransportType.CAR, loc=home)
    print("Vehicle in current position:", v)
    work = Location(lat=37.9838, lng=23.7275)
    v.set_location(work)
    print("Vehicle in new position:    ", v)

    # Weather
    print("\nWeather and Traffic Conditions")
    weather = WeatherConditions(isRaining=False, isWindy=True)
    print(
        "weather.isRaining:", weather.isRaining, ", weather.isWindy:", weather.isWindy
    )
    # Ataturk Bridge
    traffic = TrafficConditions([Location(lat=41.024268, lng=28.965210)])
    print("\nTraffic:", traffic)

    # User
    u = User(1, SexValue.MALE, AgeGroupValue.ADULT)
    print("\nUser:", u)

    # Temp Data
    t = TempData(1, 5)
    print("\nDayTime:", t)
    print("\nDayTime:", TempData.from_datetime(datetime.now()))


# TODO: We may need to enrich them with additional data
# such as battery/fuel levels

# TODO: (2) We may need to define subclass PublicTransportStops that
# have a List with the lines .. and the next stop(s) they go
