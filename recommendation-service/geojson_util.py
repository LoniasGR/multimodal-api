# ----------------------------------------------------------------------------------------
# Help Visualize Data (in a Map) using GeoJSON
# ----------------------------------------------------------------------------------------

from __future__ import annotations
from typing import Sequence, Union, Dict, Any, Optional
import json
import re
import geojson
import networkx as nx
import pyperclip
from .helpers import getObj
from .data_structures import Vehicle, TransportType, Stop, StopType, Point
from .ext_service import directions, match_profile

# ===================================== VERSION 1 =====================================

# Expect these classes/enums to be available from your model:
# from your_module import Point, Vehicle, Stop, StopType, TransportType

POI = Union["Point", "Vehicle", "Stop"]

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

# Base colors per high-level category
BASE_CATEGORY_COLORS: Dict[str, str] = {
    "Point": "#b70600",  # blue
    "Vehicle": "#878787",  # orange
    "Stop": "#2d2d2d",  # green
}

# Optional subtype-specific palettes
STOP_TYPE_COLORS: Dict["StopType", str] = {
    StopType.SCOOTER_STOP: "#004701",
    StopType.CAR_STOP: "#703a00",
    StopType.BUS_STOP: "#3b3b3b",
    StopType.SEA_VESSEL_STOP: "#05006b",
}
VEHICLE_TYPE_COLORS: Dict["TransportType", str] = {
    TransportType.FOOT: "#7f7f7f",
    TransportType.SCOOTER: "#10bd00",
    TransportType.CAR: "#c06600",
    TransportType.BUS: "#6b6b6b",
    TransportType.SEA_VESSEL: "#1f77b4",
}


def _valid_hex(color: str) -> bool:
    return isinstance(color, str) and bool(_HEX.match(color))


def _color_for_poi(
    poi: POI,
    *,
    use_subtype_colors: bool,
    color_overrides: Optional[Dict[str, str]],
) -> str:
    """Why: stable coloring across sessions; per-subtype when requested."""
    # 1) explicit overrides by keys: category ("Point"/"Vehicle"/"Stop"),
    #    or enum names like "BUS_STOP", "CAR", etc.
    if color_overrides:
        # per-subtype override first
        if isinstance(poi, Stop):
            key = getattr(poi.type, "name", None)
            if key and key in color_overrides and _valid_hex(color_overrides[key]):
                return color_overrides[key]
        if isinstance(poi, Vehicle):
            key = getattr(poi.type, "name", None)
            if key and key in color_overrides and _valid_hex(color_overrides[key]):
                return color_overrides[key]
        # per-category override
        cat = type(poi).__name__
        if cat in color_overrides and _valid_hex(color_overrides[cat]):
            return color_overrides[cat]

    # 2) subtype maps (if enabled)
    if use_subtype_colors:
        if isinstance(poi, Stop) and STOP_TYPE_COLORS:
            c = STOP_TYPE_COLORS.get(poi.type)
            if c and _valid_hex(c):
                return c
        if isinstance(poi, Vehicle) and VEHICLE_TYPE_COLORS:
            c = VEHICLE_TYPE_COLORS.get(poi.type)
            if c and _valid_hex(c):
                return c

    # 3) category default
    c = BASE_CATEGORY_COLORS.get(type(poi).__name__)
    return c if _valid_hex(c) else "#000000"


def pois_to_geojson(
    pois: Sequence[POI],
    *,
    use_subtype_colors: bool = True,
    color_overrides: Optional[Dict[str, str]] = None,
) -> str:
    """
    Convert a list of Point | Vehicle | Stop to a GeoJSON FeatureCollection string.
    Adds styling via 'marker-color', plus 'stroke'/'fill'.
    """
    if not isinstance(pois, (list, tuple)):
        raise TypeError("pois must be a list/tuple of Point | Vehicle | Stop")

    features = []
    for idx, poi in enumerate(pois):
        if not isinstance(poi, (Point, Vehicle, Stop)):
            raise TypeError(f"pois[{idx}] must be Point, Vehicle, or Stop")

        loc = getattr(poi, "loc", None)
        if loc is None or not hasattr(loc, "lat") or not hasattr(loc, "lng"):
            raise TypeError(f"pois[{idx}].loc must be a Location with lat and lng")

        lat = getattr(loc, "lat")
        lng = getattr(loc, "lng")
        if not isinstance(lat, float) or not isinstance(lng, float):
            raise TypeError(f"pois[{idx}].loc.lat/lng must be float")

        geometry: Dict[str, Any] = {"type": "Point", "coordinates": [lng, lat]}

        props: Dict[str, Any] = {"category": type(poi).__name__}

        if hasattr(poi, "uid") and callable(getattr(poi, "uid")):
            try:
                props["uid"] = poi.uid()
            except Exception:
                pass

        if hasattr(poi, "name"):
            name_val = getattr(poi, "name")
            if isinstance(name_val, str) and name_val.strip():
                props["name"] = name_val

        if isinstance(poi, Stop):
            props["stop_id"] = poi.id
            props["stop_type"] = str(poi.type)
            if hasattr(poi.type, "abbr"):
                props["stop_type_abbr"] = poi.type.abbr()
        elif isinstance(poi, Vehicle):
            props["vehicle_id"] = poi.id
            props["vehicle_type"] = str(poi.type)
            if hasattr(poi.type, "abbr"):
                props["vehicle_type_abbr"] = poi.type.abbr()

        color = _color_for_poi(
            poi, use_subtype_colors=use_subtype_colors, color_overrides=color_overrides
        )
        props["marker-color"] = color
        props["stroke"] = color
        props["fill"] = color

        feature: Dict[str, Any] = {
            "type": "Feature",
            "id": props.get("uid"),
            "geometry": geometry,
            "properties": props,
        }
        features.append(feature)

    collection = {"type": "FeatureCollection", "features": features}
    return json.dumps(collection, ensure_ascii=False, separators=(",", ":"))


# ===================================== VERSION 2 =====================================


def create_vehicle_feature(v: Vehicle) -> geojson.Feature:
    properties = {}
    properties["type"] = str(v.type)
    properties["id"] = v.id
    # properties["battery"] = 100  # TODO: Implement real values
    # properties["is_dummy"] = False  # TODO: Implement real values

    match v.type.name:
        case "SCOOTER":
            properties["marker-symbol"] = "scooter"
            properties["marker-color"] = "#45b93b"
        case "BUS":
            properties["marker-symbol"] = "bus"
            properties["marker-color"] = "#818181"
        case "CAR":
            properties["marker-symbol"] = "car"
            properties["marker-color"] = "#b57123"
        case "SEA_VESSEL":
            properties["marker-symbol"] = "ferry"
            properties["marker-color"] = "#1f77b4"
        case _:
            raise Exception(f"Not implemented yet {v}")

    point = geojson.Point(v.loc.to_tuple(reversed=True))
    return geojson.Feature(geometry=point, properties=properties)


def create_stop_feature(s: Stop) -> geojson.Feature:
    properties = {}
    properties["type"] = str(s.type)
    properties["id"] = s.id
    # TODO: update it for stops
    match s.type.name:
        case "SEA_VESSEL_STOP":
            properties["marker-symbol"] = "harbor"
            properties["marker-color"] = "#8ca9bd"
        case "CAR_STOP":
            properties["marker-symbol"] = "car"
            properties["marker-color"] = "#c7b9a9"
        case "SCOOTER_STOP":
            properties["marker-symbol"] = "scooter"
            properties["marker-color"] = "#a8c3a5"
        case "BUS_STOP":
            properties["marker-symbol"] = "bus"
            properties["marker-color"] = "#c1c1c1"
        case _:
            raise Exception(f"Not implemented yet {s}")

    point = geojson.Point(s.loc.to_tuple(reversed=True))
    return geojson.Feature(geometry=point, properties=properties)


def create_point_feature(p: Point) -> geojson.Feature:
    properties = {}
    properties["type"] = str(p.type)
    properties["name"] = p.name

    match p.name:
        case "START":
            properties["marker-symbol"] = "arrow"
            properties["marker-color"] = "#e78787"
        case "END":
            properties["marker-symbol"] = "circle-stroked"
            properties["marker-color"] = "#fd4343"
        case _:
            raise Exception(f"Not implemented yet {p}")

    point = geojson.Point(p.loc.to_tuple(reversed=True))
    return geojson.Feature(geometry=point, properties=properties)


def generate_poi_features(pois: list) -> list[geojson.Feature]:
    features = []
    for poi in pois:
        match poi:
            case Vehicle():
                features.append(create_vehicle_feature(poi))
            case Stop():
                features.append(create_stop_feature(poi))
            case Point():
                features.append(create_point_feature(poi))
            case _:
                raise Exception(f"Unknown entity type {poi}")
    return features


def generate_poi_geojson(pois: list) -> geojson.FeatureCollection:
    features = generate_poi_features(pois)
    return geojson.FeatureCollection(features=features)


def visualize_pois(pois: list, toPrint=False, toClipboard=True, toFile=None) -> None:
    json_str = geojson.dumps(generate_poi_geojson(pois), indent=2)
    if toPrint:
        print(json_str)
    if toClipboard:
        pyperclip.copy(json_str)
        print("\n * geojson save to clipboard !\n")
    if toFile:
        with open(toFile, "w") as f:
            f.write(json_str)
        # print(f" * geojson save to file: {toFile} !")


def create_line(start, stop, mot, true_paths=True) -> geojson.Feature:
    match mot:
        case TransportType.FOOT:
            color = "#7f7f7f"
        case TransportType.SCOOTER:
            color = "#10bd00"
        case TransportType.CAR:
            color = "#c06600"
        case TransportType.BUS:
            color = "#6b6b6b"
        case TransportType.SEA_VESSEL:
            color = "#1f77b4"
        case _:
            raise Exception(f"Not implemented yet {mot}")
    if mot != TransportType.SEA_VESSEL and true_paths:
        profile = match_profile(mot)
        (_, geometry) = directions(
            start.loc.to_tuple(reversed=True),
            stop.loc.to_tuple(reversed=True),
            profile=profile,
            output="summary",
        )
    else:
        geometry = [
            [start.loc.lng, start.loc.lat],
            [stop.loc.lng, stop.loc.lat],
        ]
    line = geojson.LineString(geometry, stroke=color)
    feature = geojson.Feature(
        geometry=line, properties={"stroke": color, "stroke-width": 4}
    )
    return feature


"""
def create_path_features(path: list, pois: list, graph: nx.Graph) -> list[geojson.Feature]:
    features = []
    for pair in nx.utils.pairwise(path):
        edge = graph.get_edge_data(pair[0], pair[1])
        feature = create_line(pair[0], pair[1], edge.get("mot"))
        features.append(feature)
    return features

def visualize_pois_and_links(pois: list, paths: list, graph: nx.Graph) -> None:
    # Nodes
    nodes_geojson = generate_poi_features(pois)
    # Edges
    paths_geojson = []
    # TODO: Define which paths to visualize
    for path in paths[3:4]:
        edges_geojson = create_path_features(path, pois, graph)
        paths_geojson.extend(edges_geojson)

    final_geojson = paths_geojson.copy()
    final_geojson.extend(nodes_geojson)

    print("\n * geojson save to clipboard !\n")
    collection = geojson.FeatureCollection(features=final_geojson)
    pyperclip.copy(geojson.dumps(collection, indent=2))


def visualize_graph(graph: nx.Graph) -> geojson.FeatureCollection:
    nodes = graph.nodes()
    pois = generate_poi_features(nodes)

    edges = graph.edges(data=True)
    lines = []
    for s, d, data in edges:
        line = create_line(s, d, data.get("mot"), true_paths=False)
        lines.append(line)
    collection = geojson.FeatureCollection(features=pois + lines)
    pyperclip.copy(geojson.dumps(collection, indent=2))
    return collection
"""


def visualize_graph(
    objs: list, graph: nx.Graph, toPrint=False, toClipboard=True, toFile=None
) -> None:
    # Graph Nodes
    pois = []
    for node in list(graph.nodes):
        pois.append(getObj(node, objs))
    nodes_geojson = generate_poi_features(pois)

    # Graph Edges
    edges_geojson = []
    for u, v, attrs in graph.edges(data=True):
        a = getObj(u, pois)
        b = getObj(v, pois)
        e_mot = attrs["mot"]
        line = create_line(a, b, e_mot, False)
        edges_geojson.append(line)

    final_geojson = nodes_geojson.copy()
    final_geojson.extend(edges_geojson.copy())

    collection = geojson.FeatureCollection(features=final_geojson)

    json_str = geojson.dumps(collection, indent=2)
    if toPrint:
        print(json_str)
    if toClipboard:
        pyperclip.copy(json_str)
        print("\n * geojson save to clipboard !\n")
    if toFile:
        with open(toFile, "w") as f:
            f.write(json_str)


# Visualize both Entities (incl. new ones) and Links
# Attention:
# (1) The Sea Vessels should be presented in graph. Nevertheless they are not used in Paths since we focus on Ports
# (2) Some additional nodes were often added (i.e., for Scooters Stop)


def visualize_pois_and_links(
    pois: list,
    paths: list,
    graph: nx.Graph,
    true_paths=False,
    toPrint=False,
    toClipboard=True,
    toFile=None,
    toReturn=False,
) -> None:
    # TODO: Remove Scooter Stops (from POIs) not in Paths

    # Nodes
    nodes_geojson = generate_poi_features(pois)

    # Edges
    lines = []
    for path in paths:
        for tuple in nx.utils.pairwise(path):
            a = getObj(tuple[0], pois)
            b = getObj(tuple[1], pois)
            e_mot = graph.get_edge_data(tuple[0], tuple[1]).get("mot")
            line = create_line(a, b, e_mot, true_paths)
            lines.append(line)
            # print(line)

    final_geojson = nodes_geojson.copy()
    final_geojson.extend(lines.copy())

    collection = geojson.FeatureCollection(features=final_geojson)

    json_str = geojson.dumps(collection, indent=2)
    if toPrint:
        print(json_str)
    if toClipboard:
        pyperclip.copy(json_str)
        print("\n * geojson save to clipboard !\n")
    if toFile:
        with open(toFile, "w") as f:
            f.write(json_str)
        # print(f" * geojson save to file: {toFile} !")
    if toReturn:
        return json_str


# ----------------------------------------------------------------------------------------
