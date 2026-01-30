from .location import Location
from .point import Point
from .recommendation_request import (
    RecommendationRequestPublic,
    RecommendationRequest,
    RecommendationRequestBase,
)
from .stop import Stop, StopBase, StopDB
from .stop_type import StopType
from .transport_type import TransportType
from .trip import Trip, TripPublicWithVehicles
from .trip_vehicle import TripVehicle, TripVehiclePublicWithVehicle
from .user import User, UserBase
from .vehicle import (
    VehiclePublic,
    VehicleBase,
    Vehicle,
    VehicleCreate,
    VehicleWithEvent,
    VehicleWithAllEvents,
)
from .environmental_conditions import EnvironmentalConditions
from .traffic import Traffic
from .vehicle_event import VehicleEventBase, VehicleEvent
from .suggestion import Suggestion, SuggestionBase, SuggestionPublic
from .token import Token, TokenData

TripVehiclePublicWithVehicle.model_rebuild()
TripPublicWithVehicles.model_rebuild()
VehicleWithEvent.model_rebuild()
VehicleWithAllEvents.model_rebuild()

__all__ = [
    "Location",
    "Point",
    "StopBase",
    "RecommendationRequestBase",
    "RecommendationRequestPublic",
    "RecommendationRequest",
    "StopDB",
    "Trip",
    "TripPublicWithVehicles",
    "TripVehicle",
    "TripVehiclePublicWithVehicle",
    "User",
    "UserBase",
    "VehicleBase",
    "Vehicle",
    "VehicleCreate",
    "EnvironmentalConditions",
    "Traffic",
    "VehicleEventBase",
    "VehicleEvent",
    "VehicleWithEvent",
    "VehicleWithAllEvents",
    "Suggestion",
    "SuggestionBase",
    "SuggestionPublic",
    "Token",
    "TokenData",
]


def isPoint(o):
    return isinstance(o, Point)


def isStartPoint(o):
    return isinstance(o, Point) and o.name == "START"


def isEndPoint(o):
    return isinstance(o, Point) and o.name == "END"


def isVehicle(o):
    return isinstance(o, VehiclePublic)


def isCar(o):
    return isinstance(o, VehiclePublic) and o.type == TransportType.CAR


def isBus(o):
    return isinstance(o, VehiclePublic) and o.type == TransportType.BUS


def isScooter(o):
    return isinstance(o, VehiclePublic) and o.type == TransportType.SCOOTER


def isSeaVessel(o):
    return isinstance(o, VehiclePublic) and o.type == TransportType.SEA_VESSEL


def isStop(o):
    return isinstance(o, Stop)


def isCarStop(o):
    return isinstance(o, Stop) and o.type == StopType.CAR_STOP


def isBusStop(o):
    return isinstance(o, Stop) and o.type == StopType.BUS_STOP


def isScooterStop(o):
    return isinstance(o, Stop) and o.type == StopType.SCOOTER_STOP


def isSeaVesselStop(o):
    return isinstance(o, Stop) and o.type == StopType.SEA_VESSEL_STOP


if __name__ == "__main__":
    # Location (and distance)
    print("\nLocation (and distance):")
    athens = Location(
        latitude=37.983810, longitude=23.727539
    )  # Position(lat=38.0, lng=23.0)
    print("Location of Athens:", athens)
    rome = Location(latitude=41.902782, longitude=12.496366)
    print("Location of Rome:", rome)
    print("Athens-Rome distance(m):", athens.distance_to(rome))

    # Point
    print("\nPoint:")
    loc_home = Location(latitude=37.9838, longitude=23.7275)  # Athens
    home = Point(name="Home", loc=loc_home)
    print("Point:", home)

    # Stop and Stop Types
    print("\nStop and Stop Types:")
    for mode in StopType:
        print(f"{mode!s} = {int(mode)}")

    center = Location(latitude=37.9838, longitude=23.7275)
    s = Stop(id=1, name="Syntagma", type=StopType.BUS_STOP, loc=center)
    print("Stop", s)

    # Vehicle and Modes of Transport
    print("\nVehicle and Modes of Transport")
    for mode in TransportType:
        print(f"{mode!s} = {int(mode)}")

    home = Location(latitude=37.9755, longitude=23.7348)
    v = VehiclePublic(id=1, type=TransportType.CAR)
    v.set_location(home)
    print("Vehicle in current position:", v)
    work = Location(latitude=37.9838, longitude=23.7275)
    print("Vehicle in new position:    ", v)


# TODO: We may need to enrich them with additional data
# such as battery/fuel levels

# TODO: (2) We may need to define subclass PublicTransportStops that
# have a List with the lines .. and the next stop(s) they go
