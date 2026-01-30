from typing import List, Dict, Tuple, Union

from data_structures import Location
from data_structures import Point
from data_structures import TransportType
from data_structures import Vehicle
from data_structures import StopType
from data_structures import Stop


def make_sample_vehicles() -> List[Vehicle]:
    vehicles: List[Vehicle] = []

    escooters: List[Vehicle] = [
        # UnCommented
        # Vehicle(id=11, type=TransportType.SCOOTER, loc=Location(lat=41.013269614600254, lng=28.982343636017823)),
        Vehicle(
            id=12,
            type=TransportType.SCOOTER,
            loc=Location(lat=41.01314027200971, lng=28.98150460492709),
        ),
        # UnCommented
        # Vehicle(id=13, type=TransportType.SCOOTER, loc=Location(lat=41.01277597931744, lng=28.98191512922669)),
        # Vehicle(id=14, type=TransportType.SCOOTER, loc=Location(lat=41.00563519866201, lng=28.975351380519545)),
        # Vehicle(id=15, type=TransportType.SCOOTER, loc=Location(lat=41.00566309991613, lng=28.974784465907696)),
        # Vehicle(id=16, type=TransportType.SCOOTER, loc=Location(lat=41.006342026791756, lng=28.975647162056156)),
        Vehicle(
            id=17,
            type=TransportType.SCOOTER,
            loc=Location(lat=41.005960712558284, lng=28.97567181051754),
        ),
        Vehicle(
            id=18,
            type=TransportType.SCOOTER,
            loc=Location(lat=41.025828707631824, lng=28.97382556255339),
        ),
    ]
    vehicles.extend(escooters)

    cars: List[Vehicle] = [
        Vehicle(
            id=21,
            type=TransportType.CAR,
            loc=Location(lat=41.01868321638535, lng=28.969173221308647),
        ),
        Vehicle(
            id=22,
            type=TransportType.CAR,
            loc=Location(lat=41.03069128613904, lng=28.97889099614874),
        ),
        Vehicle(
            id=23,
            type=TransportType.CAR,
            loc=Location(lat=41.03067966506559, lng=28.978874050377),
        ),
    ]
    vehicles.extend(cars)

    sea_vessels: List[Vehicle] = [
        Vehicle(
            id=31,
            type=TransportType.SEA_VESSEL,
            loc=Location(lat=41.0189046080869, lng=28.970296414795676),
        ),
        Vehicle(
            id=32,
            type=TransportType.SEA_VESSEL,
            loc=Location(lat=41.01893834912678, lng=28.970219170891095),
        ),
    ]
    vehicles.extend(sea_vessels)

    return vehicles


def make_sample_stops() -> List[Stop]:
    stops: List[Stop] = [
        # Parkings
        Stop(
            id=11,
            name="Sports Car Park",
            type=StopType.CAR_STOP,
            loc=Location(lat=41.00948, lng=28.9771898),
        ),
        Stop(
            id=12,
            name="Eminonu Vale Otopark hizmetleri",
            type=StopType.CAR_STOP,
            loc=Location(lat=41.0187618, lng=28.9691456),
        ),
        Stop(
            id=13,
            name="Teo Otopark",
            type=StopType.CAR_STOP,
            loc=Location(lat=41.0306583, lng=28.9789037),
        ),
        # Ports
        Stop(
            id=21,
            name="Eminonu Port",
            type=StopType.SEA_VESSEL_STOP,
            loc=Location(lat=41.0188405651898, lng=28.970441186161192),
        ),
        Stop(
            id=22,
            name="Karakoy Port",
            type=StopType.SEA_VESSEL_STOP,
            loc=Location(lat=41.021854, lng=28.973367),
        ),
        Stop(
            id=23,
            name="Kasimpasa Port",
            type=StopType.SEA_VESSEL_STOP,
            loc=Location(lat=41.03041, lng=28.96623),
        ),
    ]
    return stops


def user_sample_start_end_positions() -> Tuple[Location, Location]:
    points: List[Point] = [
        # Point("START", Location(41.00821728552505, 28.983291711081748)),
        Point(
            "START", Location(41.00541738656229, 28.981464735247233)
        ),  # Royan Hotel Hagia Sophia Istanbul
        Point(
            "END", Location(lat=41.0259196, lng=28.9828383)
        ),  # Istanbul Modern Museum
    ]
    return points


def get_pois():
    # Sample Data - Current Status and User's start/stop
    vehicles = make_sample_vehicles()
    stops = make_sample_stops()
    points = user_sample_start_end_positions()
    # A List with all of them
    objs = Union[Point, Vehicle, Stop]
    objs = list(points) + list(vehicles) + list(stops)
    return objs
