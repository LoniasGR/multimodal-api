from dataclasses import dataclass
from enum import IntEnum


class TransportType(IntEnum):
    """Means of Transport"""

    FOOT = 1
    SCOOTER = 2  # e-scooter
    CAR = 3  # e-car
    BUS = 4
    SEA_VESSEL = 5


@dataclass
class Location:
    lat: float
    lng: float


@dataclass
class Vehicle:
    id: int
    type: TransportType
    loc: Location
    is_available: bool = True  # new field (default: available)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type.name,
            "location": {"latitude": self.loc.lat, "longitude": self.loc.lng},
            "is_available": self.is_available,
        }


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


def make_sample_vehicles() -> list[Vehicle]:
    vehicles: list[Vehicle] = []

    escooters: list[Vehicle] = [
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

    cars: list[Vehicle] = [
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

    sea_vessels: list[Vehicle] = [
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


def make_sample_stops() -> list[Stop]:
    stops: list[Stop] = [
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


def submit_vehicle(vehicle: Vehicle, url="http://127.0.0.1:8000/vehicles"):
    import requests

    exists = requests.get(f"{url}/{vehicle.id}")

    if exists.status_code == 200:
        print(f"Vehicle {vehicle.id} already exists. Skipping submission.")
        return

    response = requests.post(url, json=vehicle.to_dict())
    if response.status_code == 201:
        print(f"Vehicle {vehicle.id} submitted successfully.")
    else:
        print(
            f"Failed to submit Vehicle {vehicle.id}. Status code: {response.status_code}"
        )


def submit_stop(stop: Stop, url="http://127.0.0.1:8000/stops"):
    import requests

    stop_data = {
        "name": stop.name,
        "type": stop.type.name,
        "location": {"latitude": stop.loc.lat, "longitude": stop.loc.lng},
    }
    response = requests.post(url, json=stop_data)
    if response.status_code == 201:
        print(f"Stop {stop.id} submitted successfully.")
    else:
        print(f"Failed to submit Stop {stop.id}. Status code: {response.status_code}")


if __name__ == "__main__":
    TARGET_URL = "http://147.102.19.14:8000"
    vehicles = make_sample_vehicles()
    for vehicle in vehicles:
        submit_vehicle(vehicle, f"{TARGET_URL}/vehicles")
    stops = make_sample_stops()
    for stop in stops:
        submit_stop(stop, f"{TARGET_URL}/stops")
