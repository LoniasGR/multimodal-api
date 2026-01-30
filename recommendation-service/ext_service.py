# ----------------------------------------------------------------------------------------
# Services that make use of Open Street Maps API for
# retrieving the expected duration and distance for car(or bus)/scooter/walk
# ----------------------------------------------------------------------------------------

import functools

import requests
from openrouteservice.directions import directions as ors_directions

import openrouteservice

from .config import *
from .data_structures import Location, TransportType

client = openrouteservice.Client(base_url=ORS_URL)

# Method 1


@functools.cache
def snap(
    locations: Location | list[Location],
    profile="driving-car",
    radius=300,
    format="json",
):
    if isinstance(locations, Location):
        loc = [locations]
    else:
        loc = locations
    r = client.request(
        url=f"/v2/snap/{profile}/{format}",
        post_json={
            "locations": list(map(lambda x: x.to_list(reversed=True), loc)),
            "radius": radius,
        },
    )
    if isinstance(locations, Location):
        return Location.from_list(r["locations"][0]["location"], reversed=True)
    else:
        return [
            Location.from_list(l["location"], reversed=True) for l in r["locations"]
        ]


# Method 2


@functools.cache
def getTransData(start, end, mot):
    if mot == TransportType.SEA_VESSEL:
        distance = start.distance_to(end)
        duration = distance / AVG_SEA_VESSEL_VELOCITY
        return (
            {"distance": distance, "duration": duration},
            [[start.lat, start.lng], [end.lat, end.lng]],
        )

    if mot == TransportType.CAR or mot == TransportType.BUS:
        url = "http://147.102.19.14:8082/ors/v2/directions/driving-car"
    elif mot == TransportType.FOOT:
        url = "http://147.102.19.14:8082/ors/v2/directions/foot-walking"
    elif mot == TransportType.SCOOTER:
        url = "http://147.102.19.14:8082/ors/v2/directions/cycling-electric"
    else:
        raise ValueError("mot must be a TransportType")

    start_loc = f"{start.lng}%2C{start.lat}"  # f"{start.lat}%2C{start.lng}"
    end_loc = f"{end.lng}%2C{end.lat}"  # f"{end.lat}%2C{end.lng}"
    get_url = f"{url}?start={start_loc}&end={end_loc}"
    # print(get_url)
    try:
        r = requests.get(get_url)
        feature = r.json()["features"][0]
        summary = feature["properties"]["summary"]
        geometry = feature["geometry"]["coordinates"]
        return (summary, geometry)
    except:
        return (-1, [])


@functools.cache
def directions(
    start_loc: tuple, end_loc: tuple, profile: str, format="geojson", output="summary"
):
    coords = (start_loc, end_loc)
    try:
        dirs = ors_directions(client, coords, profile=profile, format=format)
    except Exception as e:
        print(f"Fetching directions failed: {e}")
        return None
    # Summary only works with geojson format
    if format == "geojson" and output == "summary":
        summary = dirs["features"][0]["properties"]["summary"]
        geometry = dirs["features"][0]["geometry"]["coordinates"]
        return (summary, geometry)
    else:
        return dirs


@functools.cache
def getTransData2(start: Location, end: Location, mot: TransportType):
    if mot == TransportType.SEA_VESSEL:
        distance = start.distance_to(end)
        duration = distance / AVG_SEA_VESSEL_VELOCITY
        return (
            {"distance": distance, "duration": duration},
            [[start.lat, start.lng], [end.lat, end.lng]],
        )

    if mot == TransportType.CAR or mot == TransportType.BUS:
        profile = "driving-car"
    elif mot == TransportType.FOOT:
        profile = "foot-walking"
    elif mot == TransportType.SCOOTER:
        profile = "cycling-electric"
    else:
        raise ValueError("mot must be a TransportType")

    start_loc = start.to_tuple(reversed=True)
    end_loc = end.to_tuple(reversed=True)
    try:
        return directions(start_loc, end_loc, profile)
    except:
        return (-1, [])


def match_profile(mot: TransportType) -> str:
    match mot:
        case TransportType.BUS | TransportType.CAR:
            return "driving-car"
        case TransportType.FOOT:
            return "foot-walking"
        case TransportType.SCOOTER:
            return "cycling-electric"
        case _:
            raise ValueError("mot must be a TransportType")


# ----------------------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n>> Testying: snap(..)\n")
    loc_a = Location(41.04207750742227, 28.932494382685018)
    loc_b = Location(41.045456169448975, 28.93971817235892)

    loc_a_snap = snap(loc_a)
    print("loc_a:", loc_a)
    print("loc_a_snap:", loc_a_snap)
    print("\tdistance:", f"{loc_a.distance_to(loc_a_snap):.2f} meters")

    # loc_b_snap = snap([loc_b])
    # print("loc_b:", loc_b)
    # print("[loc_b_snap]:", loc_b_snap)

    print("\n>> Testying: getTransData(..)\n")
    start = Location(lat=41.04033, lng=29.0471)
    end = Location(lat=41.01094, lng=28.9781)
    print("start:", start)
    print("end:", end)

    for mode in TransportType:
        r = getTransData(start, end, mode)
        print(mode, r[0], len(r[1]))

    for mode in TransportType:
        r = getTransData2(start, end, mode)
        print(mode, r[0], len(r[1]))
        print(r[1])
        break
