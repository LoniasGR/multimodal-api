import geojson
from typing import Sequence, TypeAlias


from ..models import Point, StopPublic, VehiclePublic, TransportType
from ..openrouteservice import directions, match_profile

POI: TypeAlias = VehiclePublic | StopPublic | Point


def create_vehicle_feature(v: VehiclePublic) -> geojson.Feature:
    if v.location is None:
        raise Exception(f"Vehicle {v.id} has no location")

    properties = {}
    properties["type"] = str(v.type)
    properties["id"] = v.id

    match v.type.name:
        case "SCOOTER":
            properties["marker-symbol"] = "scooter"
            properties["marker-color"] = "#10bd00"
        case "CAR":
            properties["marker-symbol"] = "car"
            properties["marker-color"] = "#c06600"
        case "SEA_VESSEL":
            properties["marker-symbol"] = "ferry"
            properties["marker-color"] = "#1f77b4"
        case _:
            raise Exception(f"Not implemented yet {v}")

    point = geojson.Point(v.location.to_tuple(reversed=True))
    return geojson.Feature(geometry=point, properties=properties)


def create_stop_feature(s: StopPublic) -> geojson.Feature:
    properties = {}
    properties["type"] = str(s.type)
    properties["id"] = s.id
    # TODO: update it for stops
    match s.type.name:
        case "SEA_VESSEL_STOP":
            properties["marker-symbol"] = "harbor"
            properties["marker-color"] = "#121daf"
        case "BUS_STOP":
            properties["marker-symbol"] = "bus"
            properties["marker-color"] = "#1eff00"
        case "SCOOTER_STOP":
            properties["marker-symbol"] = "charging-station"
            properties["marker-color"] = "#818B80"
        case "CAR_STOP":
            properties["marker-symbol"] = "parking"
            properties["marker-color"] = "#547586"
        case _:
            raise Exception(f"Not implemented yet {s}")

    point = geojson.Point(s.location.to_tuple(reversed=True))
    return geojson.Feature(geometry=point, properties=properties)


def create_point_feature(p: Point) -> geojson.Feature:
    properties = {}
    properties["type"] = str(p.type)
    properties["name"] = p.name

    match p.name:
        case "START":
            properties["marker-symbol"] = "arrow"
            properties["marker-color"] = "#bd0000"
        case "END":
            properties["marker-symbol"] = "circle-stroked"
            properties["marker-color"] = "#bd0000"
        case _:
            raise Exception(f"Not implemented yet {p}")

    point = geojson.Point(p.location.to_tuple(reversed=True))
    return geojson.Feature(geometry=point, properties=properties)


def generate_poi_features(
    pois: Sequence[POI],
) -> list[geojson.Feature]:
    features: list[geojson.Feature] = []
    for poi in pois:
        match poi:
            case VehiclePublic():
                features.append(create_vehicle_feature(poi))
            case StopPublic():
                features.append(create_stop_feature(poi))
            case Point():
                features.append(create_point_feature(poi))
            case _:
                raise Exception(f"Unknown entity type {poi}")
    return features


def generate_poi_geojson(
    pois: Sequence[POI],
) -> geojson.FeatureCollection:
    features = generate_poi_features(pois)
    return geojson.FeatureCollection(features=features)


def create_line(
    start: POI, stop: POI, mot: TransportType, true_paths=True
) -> geojson.Feature:
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
            start.location.to_tuple(reversed=True),
            stop.location.to_tuple(reversed=True),
            profile=profile,
            format="geojson",
            output="summary",
        )
    else:
        geometry = [
            [start.location.longitude, start.location.latitude],
            [stop.location.longitude, stop.location.latitude],
        ]
    line = geojson.LineString(geometry, stroke=color)
    feature = geojson.Feature(
        geometry=line, properties={"stroke": color, "stroke-width": 4}
    )
    return feature


# # TODO: LEONIDAS
# def visualize_pois_and_links(pois: list, paths: list, graph: nx.Graph) -> None:
#     # Nodes
#     nodes_geojson = generate_poi_features(pois)
#     # Edges
#     paths_geojson = []
#     # TODO: Define which paths to visualize
#     for path in paths[3:4]:
#         edges_geojson = create_path_features(path, pois, graph)
#         paths_geojson.extend(edges_geojson)

#     final_geojson = paths_geojson.copy()
#     final_geojson.extend(nodes_geojson)

#     print("\n * geojson save to clipboard !\n")
#     collection = geojson.FeatureCollection(features=final_geojson)
#     pyperclip.copy(geojson.dumps(collection, indent=2))


# def visualize_graph(graph: nx.Graph) -> geojson.FeatureCollection:
#     nodes = graph.nodes()
#     pois = generate_poi_features(nodes)

#     edges = graph.edges(data=True)
#     lines = []
#     for s, d, data in edges:
#         line = create_line(s, d, data.get("mot"), true_paths=False)
#         lines.append(line)
#     collection = geojson.FeatureCollection(features=pois + lines)
#     pyperclip.copy(geojson.dumps(collection, indent=2))
#     return collection
