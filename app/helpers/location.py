import math

import numpy as np

from ..models import Location
from ..openrouteservice import snap


rng = np.random.default_rng()


def point_generation(original_loc: Location, radius: int):
    distance = abs(rng.normal(0, radius))
    distance = min(distance, radius)

    # Random angle (uniform distribution)
    angle = np.random.uniform(0, 2 * math.pi)

    # Convert polar to Cartesian coordinates
    dx = distance * math.cos(angle)
    dy = distance * math.sin(angle)
    new_lat, new_lng = _meters_to_lat_lng(
        dx, dy, original_loc.latitude, original_loc.longitude
    )

    return snap(Location(latitude=new_lat, longitude=new_lng))


def _meters_to_lat_lng(dx, dy, center_lat, center_lng):
    """Convert meters offset back to lat/lng."""
    R = 6371000
    center_lat_rad = math.radians(center_lat)

    dlat = dy / R
    dlng = dx / (R * math.cos(center_lat_rad))

    new_lat = math.degrees(math.radians(center_lat) + dlat)
    new_lng = math.degrees(math.radians(center_lng) + dlng)

    return new_lat, new_lng
