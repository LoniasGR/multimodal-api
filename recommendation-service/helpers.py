# ----------------------------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------------------------

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Literal, Optional
import math

# Part A: Compute the coordinates of the point lying on the geodesic from A -> B

Model = Literal["geodesic", "sphere"]

def point_along_line(
    lat_a: float,
    lon_a: float,
    lat_b: float,
    lon_b: float,
    distance_m: float,
    *,
    model: Model = "geodesic",
    clamp: bool = True,
    earth_radius_m: float = 6_371_008.8,
) -> Tuple[float, float]:
    """
    Compute the coordinates of the point lying on the geodesic from A -> B
    at a given distance (meters) from A.

    Parameters
    ----------
    lat_a, lon_a : float
        Point A in degrees.
    lat_b, lon_b : float
        Point B in degrees.
    distance_m : float
        Distance from A along the geodesic toward B (meters).
    model : {"geodesic", "sphere"}, default "geodesic"
        - "geodesic": Use WGS-84 ellipsoid via geographiclib if available; falls back to sphere if not.
        - "sphere"  : Use great-circle math on a sphere of radius `earth_radius_m`.
    clamp : bool, default True
        If True, clamp `distance_m` to [0, total_distance(A,B)] to stay on the segment (not beyond B).
        If False, allow extrapolation past B (or before A for negative distances).
    earth_radius_m : float, default 6_371_008.8
        Mean Earth radius used for the spherical fallback.

    Returns
    -------
    (lat, lon) : tuple of floats
        Coordinates of the target point in degrees, lon normalized to [-180, 180].

    Raises
    ------
    ValueError
        If A and B are identical and distance_m > 0 (undefined direction).
    """
    # Normalize inputs early (why: avoids surprises when crossing dateline)
    lon_a = _normalize_lon(lon_a)
    lon_b = _normalize_lon(lon_b)

    if distance_m == 0:
        return (float(lat_a), _normalize_lon(float(lon_a)))

    # Prefer precise WGS-84 if requested and available
    if model == "geodesic":
        try:
            from geographiclib.geodesic import Geodesic  # type: ignore
            inv = Geodesic.WGS84.Inverse(lat_a, lon_a, lat_b, lon_b)
            total = inv["s12"]  # meters
            if math.isclose(total, 0.0, abs_tol=1e-9):
                if distance_m > 0 and clamp:
                    # A == B and clamped => return A
                    return (float(lat_a), _normalize_lon(float(lon_a)))
                raise ValueError("Points A and B are identical; direction is undefined.")
            s = distance_m
            if clamp:
                s = max(0.0, min(distance_m, total))
            # Forward azimuth from A toward B
            azi1 = inv["azi1"]
            dir_res = Geodesic.WGS84.Direct(lat_a, lon_a, azi1, s)
            return (float(dir_res["lat2"]), _normalize_lon(float(dir_res["lon2"])))
        except Exception:
            # Fallback to spherical if geographiclib not installed or failed
            pass

    # Spherical great-circle fallback (robust, dependency-free)
    lat1 = math.radians(lat_a)
    lon1 = math.radians(lon_a)
    lat2 = math.radians(lat_b)
    lon2 = math.radians(lon_b)

    # Central angle via haversine
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    h = min(1.0, max(0.0, h))  # numeric safety
    delta = 2 * math.asin(math.sqrt(h))  # central angle (rad)

    if math.isclose(delta, 0.0, abs_tol=1e-15):
        if distance_m > 0 and clamp:
            return (float(lat_a), _normalize_lon(float(lon_a)))
        raise ValueError("Points A and B are identical; direction is undefined.")

    total_dist = earth_radius_m * delta
    t = distance_m / total_dist
    if clamp:
        t = max(0.0, min(1.0, t))

    # Slerp on the unit sphere
    sin_delta = math.sin(delta)
    # If nearly antipodal or very small angles, blend guards against instability
    if math.isclose(sin_delta, 0.0, abs_tol=1e-15):
        A_w = 1.0 - t
        B_w = t
    else:
        A_w = math.sin((1 - t) * delta) / sin_delta
        B_w = math.sin(t * delta) / sin_delta

    # Convert to 3D unit vectors
    x1, y1, z1 = _ll_to_xyz(lat1, lon1)
    x2, y2, z2 = _ll_to_xyz(lat2, lon2)
    x = A_w * x1 + B_w * x2
    y = A_w * y1 + B_w * y2
    z = A_w * z1 + B_w * z2

    # Normalize vector (why: guard rounding error)
    r = math.sqrt(x * x + y * y + z * z)
    if r == 0.0:
        # Shouldn't happen unless A and B are exact antipodes and t=0.5
        # In that rare case pick a perpendicular great-circle direction
        return _antipodal_midpoint(lat1, lon1)

    x /= r
    y /= r
    z /= r

    lat = math.degrees(math.atan2(z, math.sqrt(x * x + y * y)))
    lon = math.degrees(math.atan2(y, x))
    return (lat, _normalize_lon(lon))


def _normalize_lon(lon: float) -> float:
    """Wrap longitude to [-180, 180]."""
    lon = ((lon + 180.0) % 360.0) - 180.0
    # Map -180 to 180 consistently
    return 180.0 if math.isclose(lon, -180.0, abs_tol=1e-12) else lon


def _ll_to_xyz(lat_rad: float, lon_rad: float) -> Tuple[float, float, float]:
    clat = math.cos(lat_rad)
    return (clat * math.cos(lon_rad), clat * math.sin(lon_rad), math.sin(lat_rad))


def _antipodal_midpoint(lat1: float, lon1: float) -> Tuple[float, float]:
    """Select a deterministic midpoint when A and B are antipodal and t=0.5."""
    # Pick a perpendicular vector to avoid ambiguity.
    # Choose axis roughly E-W if not near poles.
    if abs(math.cos(lat1)) > 1e-6:
        lon_mid = _normalize_lon(math.degrees(lon1 + math.pi / 2))
        return (0.0, lon_mid)
    else:
        # Near poles, choose equator at lon1
        return (0.0, _normalize_lon(math.degrees(lon1)))


# Part B: 


# ----- Types -----
LatLng = Tuple[float, float]  # (lat, lon)


@dataclass(frozen=True)
class RouteInPolygonResult:
    passes: bool
    segments: List[List[LatLng]]
    lengths_m: List[float]
    total_inside_m: float


# ----- Geo helpers -----
def _haversine_m(a: LatLng, b: LatLng) -> float:
    """Geodesic distance in meters (spherical Earth)."""
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    sin_dlat = math.sin(dlat / 2.0)
    sin_dlon = math.sin(dlon / 2.0)
    aa = sin_dlat * sin_dlat + math.cos(lat1) * math.cos(lat2) * sin_dlon * sin_dlon
    c = 2.0 * math.atan2(math.sqrt(aa), math.sqrt(max(0.0, 1.0 - aa)))
    return 6371008.8 * c  # mean Earth radius (meters)


def _polyline_length_m(polyline: List[LatLng]) -> float:
    if len(polyline) < 2:
        return 0.0
    return sum(_haversine_m(polyline[i], polyline[i + 1]) for i in range(len(polyline) - 1))


def _close_polygon_if_needed(poly: List[LatLng]) -> List[LatLng]:
    if not poly:
        return poly
    if poly[0] != poly[-1]:
        return poly + [poly[0]]
    return poly


# ----- Point-in-polygon (ray casting) -----
def _point_in_polygon(pt: LatLng, polygon: List[LatLng]) -> bool:
    """Ray casting; returns True when strictly inside or on edge."""
    lat, lon = pt
    inside = False
    n = len(polygon)
    if n < 3:
        return False

    # Treat boundary as inside: check proximity to edges
    for i in range(n - 1):
        lat1, lon1 = polygon[i]
        lat2, lon2 = polygon[i + 1]
        # Check if pt lies exactly on the segment (with tolerance)
        if _point_on_segment((lat, lon), (lat1, lon1), (lat2, lon2), tol=1e-12):
            return True

    j = n - 1
    for i in range(n):
        lat_i, lon_i = polygon[i]
        lat_j, lon_j = polygon[j]

        intersect = ((lon_i > lon) != (lon_j > lon)) and (
            lat < (lat_j - lat_i) * (lon - lon_i) / (lon_j - lon_i + 1e-300) + lat_i
        )
        if intersect:
            inside = not inside
        j = i

    return inside


def _point_on_segment(p: LatLng, a: LatLng, b: LatLng, tol: float = 1e-12) -> bool:
    """Check if point p lies on segment ab in lat-lon plane (approx; good for boundary inclusion)."""
    (py, px), (ay, ax), (by, bx) = p, a, b
    cross = (px - ax) * (by - ay) - (py - ay) * (bx - ax)
    if abs(cross) > tol:
        return False
    dot = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
    if dot < -tol:
        return False
    sq_len = (bx - ax) ** 2 + (by - ay) ** 2
    if dot - sq_len > tol:
        return False
    return True


# ----- Shapely (exact) path -----
def _with_shapely(
    route: List[LatLng],
    polygon: List[LatLng],
) -> Optional[RouteInPolygonResult]:
    try:
        from shapely.geometry import LineString, Polygon, GeometryCollection, MultiLineString
        from shapely.ops import unary_union
    except Exception:
        return None

    if len(route) < 2 or len(polygon) < 3:
        return RouteInPolygonResult(False, [], [], 0.0)

    poly_closed = _close_polygon_if_needed(polygon)

    # Shapely expects (x, y) = (lon, lat)
    route_ls = LineString([(lng, lat) for lat, lng in route])
    poly = Polygon([(lng, lat) for lat, lng in poly_closed])

    if not route_ls.is_valid or not poly.is_valid:
        # Prefer returning something sensible over raising
        return RouteInPolygonResult(False, [], [], 0.0)

    inter = route_ls.intersection(poly)

    # Normalize to iterable of LineStrings
    lines = []
    if inter.is_empty:
        lines = []
    elif isinstance(inter, LineString):
        lines = [inter]
    elif isinstance(inter, MultiLineString):
        lines = list(inter.geoms)
    elif isinstance(inter, GeometryCollection):
        lines = [g for g in inter.geoms if isinstance(g, LineString)]
    else:
        lines = []

    segments_latlng: List[List[LatLng]] = [
        [(lat, lng) for (lng, lat) in line.coords] for line in lines if len(line.coords) >= 2
    ]
    lengths = [_polyline_length_m(seg) for seg in segments_latlng]
    total = float(sum(lengths))
    return RouteInPolygonResult(passes=(total > 0.0), segments=segments_latlng, lengths_m=lengths, total_inside_m=total)


# ----- Fallback (sampling) path -----
def _lerp(a: LatLng, b: LatLng, t: float) -> LatLng:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _segment_samples(a: LatLng, b: LatLng, step_m: float) -> List[LatLng]:
    seg_len = max(_haversine_m(a, b), 1e-9)
    n = max(1, int(math.ceil(seg_len / step_m)))
    return [_lerp(a, b, i / n) for i in range(n)] + [b]


def _snap_boundary(a: LatLng, b: LatLng, polygon: List[LatLng], inside_a: bool, iters: int = 18) -> LatLng:
    """Binary search to approximate the crossing point for clearer segment ends."""
    lo, hi = 0.0, 1.0
    for _ in range(iters):
        mid = (lo + hi) / 2.0
        mpt = _lerp(a, b, mid)
        if _point_in_polygon(mpt, polygon) == inside_a:
            lo = mid
        else:
            hi = mid
    return _lerp(a, b, (lo + hi) / 2.0)


def _fallback_sample_based(
    route: List[LatLng],
    polygon: List[LatLng],
    step_m: float,
) -> RouteInPolygonResult:
    poly_closed = _close_polygon_if_needed(polygon)

    segments: List[List[LatLng]] = []
    cur: List[LatLng] = []

    # Track last sample to enable boundary snapping
    prev_pt: Optional[LatLng] = None
    prev_inside: Optional[bool] = None

    for i in range(len(route) - 1):
        a, b = route[i], route[i + 1]
        samples = _segment_samples(a, b, step_m)

        for idx, p in enumerate(samples):
            inside = _point_in_polygon(p, poly_closed)

            if prev_pt is not None and prev_inside is not None and inside != prev_inside:
                # Crossing occurred between prev_pt and p; snap boundary for cleaner segment ends.
                boundary = _snap_boundary(prev_pt, p, poly_closed, inside_a=prev_inside)
                if prev_inside:
                    # Closing an inside run
                    cur.append(boundary)
                    if len(cur) >= 2:
                        segments.append(cur)
                    cur = []
                else:
                    # Starting an inside run
                    cur = [boundary]

            # Add the current point if we're inside
            if inside:
                if not cur:
                    cur = [p]
                else:
                    # Avoid duplicates
                    if cur[-1] != p:
                        cur.append(p)

            prev_pt, prev_inside = p, inside

    # Close any trailing inside run
    if cur and len(cur) >= 2:
        segments.append(cur)

    lengths = [_polyline_length_m(seg) for seg in segments]
    total = float(sum(lengths))
    return RouteInPolygonResult(passes=(total > 0.0), segments=segments, lengths_m=lengths, total_inside_m=total)


# ----- Public API -----
def route_segments_in_polygon(
    route_points: List[LatLng],
    polygon_points: List[LatLng],
    *,
    sample_step_m: float = 15.0,
) -> RouteInPolygonResult:
    """
    Determine whether a route passes through a polygon and return inside segments.

    Args:
        route_points: Polyline as [(lat, lon), ...]. Needs ≥ 2 points.
        polygon_points: Polygon as [(lat, lon), ...]. Needs ≥ 3 points; closing is handled.
        sample_step_m: Fallback-only resolution in meters (smaller → more precise, slower).

    Returns:
        RouteInPolygonResult:
            - passes: True if any part of the route lies inside the polygon
            - segments: list of inside sub-polylines as [(lat, lon), ...]
            - lengths_m: geodesic length per inside segment
            - total_inside_m: total inside length in meters

    Notes:
        - If Shapely is installed, exact geometric intersection is used.
        - Without Shapely, an adaptive sampling method is used (approximate).
        - Lat/Lon order follows common Google Maps conventions.
    """
    if len(route_points) < 2 or len(polygon_points) < 3:
        return RouteInPolygonResult(False, [], [], 0.0)

    # Prefer exact path via Shapely if available
    exact = _with_shapely(route_points, polygon_points)
    if exact is not None:
        return exact

    # Approximate fallback
    return _fallback_sample_based(route_points, polygon_points, step_m=sample_step_m)


def getObj(uid, objs):
    for obj in objs:
        if obj.uid() == uid:
            return obj
    return None


# ----------------------------------------------------------------------------------------

LngLat = Tuple[float, float]

EARTH_RADIUS_M = 6371008.8  # mean Earth radius in meters


def _to_local_xy_m(ref: LngLat, p: LngLat) -> Tuple[float, float]:
    """
    Equirectangular projection around ref point.
    Returns (x, y) in meters.
    Good for local distance checks (small-ish areas).
    """
    ref_lng, ref_lat = ref
    lng, lat = p

    ref_lat_rad = math.radians(ref_lat)
    dlon = math.radians(lng - ref_lng)
    dlat = math.radians(lat - ref_lat)

    x = EARTH_RADIUS_M * dlon * math.cos(ref_lat_rad)
    y = EARTH_RADIUS_M * dlat
    return x, y


def _point_to_segment_distance_m(p: LngLat, a: LngLat, b: LngLat) -> float:
    """
    Approx min distance from point p to segment a-b (all lng/lat),
    computed in a local tangent plane (meters).
    """
    # Use p as local reference to reduce distortion
    px, py = 0.0, 0.0
    ax, ay = _to_local_xy_m(p, a)
    bx, by = _to_local_xy_m(p, b)

    abx, aby = (bx - ax), (by - ay)
    apx, apy = (px - ax), (py - ay)

    ab2 = abx * abx + aby * aby
    if ab2 == 0.0:
        # a and b are the same point
        return math.sqrt((px - ax) ** 2 + (py - ay) ** 2)

    # Project AP onto AB, clamp to segment [0,1]
    t = (apx * abx + apy * aby) / ab2
    if t < 0.0:
        cx, cy = ax, ay
    elif t > 1.0:
        cx, cy = bx, by
    else:
        cx, cy = ax + t * abx, ay + t * aby

    dx, dy = (px - cx), (py - cy)
    return math.sqrt(dx * dx + dy * dy)


def path_approaches_location(
    path: List[LngLat],
    location: LngLat,
    threshold_m: float,
) -> bool:
    """
    Returns True if the path passes through / comes within threshold_m
    of the given location.

    - path: list/tuple of (lng, lat) points
    - location: (lng, lat)
    - threshold_m: distance threshold in meters
    """
    if threshold_m < 0:
        raise ValueError("threshold_m must be non-negative")
    if len(path) == 0:
        return False
    if len(path) == 1:
        return _point_to_segment_distance_m(location, path[0], path[0]) <= threshold_m

    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        if _point_to_segment_distance_m(location, a, b) <= threshold_m:
            return True
    return False

# ----------------------------------------------------------------------------------------

if __name__ == "__main__":

    # Check Part A
    # Example: From Paris (48.8566, 2.3522) toward London (51.5074, -0.1278), 100 km from Paris.
    lat, lon = point_along_line(48.8566, 2.3522, 51.5074, -0.1278, 100_000.0)
    print(f"\nPoint ~100km from Paris toward London: {lat:.6f}, {lon:.6f}\n")

    # Check Part B
    # Minimal demo with a simple square polygon and a diagonal route.
    square = [(37.0, -122.0), (37.0, -121.99), (36.99, -121.99), (36.99, -122.0)]
    route = [(36.985, -122.005), (37.005, -121.985)]
    res = route_segments_in_polygon(route, square, sample_step_m=10.0)
    print("passes:", res.passes)
    print("total_inside_m:", round(res.total_inside_m, 2))
    for i, (seg, length) in enumerate(zip(res.segments, res.lengths_m), 1):
        print(f"segment {i} length {round(length,2)} m, points: {len(seg)}")


    # Check Part C
    # Path that approaches a Location
    path = [ (23.7275, 37.9838),  (23.7350, 37.9900), (23.7450, 37.9950)]
    target = (23.7360, 37.9890)
    print("approaches:", path_approaches_location(path, target, threshold_m=150))  # True/False
