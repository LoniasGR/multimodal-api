import openrouteservice
from openrouteservice.directions import directions as ors_directions

from ..models import TransportType, Location

from ..config import ORS_URL

client = openrouteservice.Client(base_url=ORS_URL)


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
            "locations": [x.to_list(reversed=True) for x in loc],
            "radius": radius,
        },
    )
    if r is None:
        raise Exception("No response from ORS snap endpoint")
    if isinstance(locations, Location):
        return Location.from_list(r["locations"][0]["location"], reversed=True)
    else:
        return [
            Location.from_list(l["location"], reversed=True) for l in r["locations"]
        ]


def match_profile(mot: TransportType) -> str:
    match mot:
        case TransportType.BUS | TransportType.CAR:
            return "driving-car"
        case TransportType.FOOT:
            return "foot-walking"
        case TransportType.SCOOTER:
            return "cycling-electric"
        case _:
            raise ValueError(f"mot must be a TransportType, got {mot}")
