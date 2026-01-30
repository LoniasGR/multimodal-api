from typing import List, Union
import time
import networkx as nx
import pandas as pd
import pickle
from .config import *
from .helpers import getObj
from .helpers import path_approaches_location
from .data_structures import *
from .graph_util import create_graph
from .ext_service import getTransData
from .geojson_util import visualize_pois, visualize_graph, visualize_pois_and_links
import sys
from sklearn.cluster import DBSCAN
import numpy as np


def count_entity_type(objs):
    points = vehicles = stops = 0
    for obj in objs:
        if isPoint(obj):
            points = points + 1
        if isVehicle(obj):
            vehicles = vehicles + 1
        if isStop(obj):
            stops = stops + 1
    return (points, vehicles, stops)


def create_path_pattern(G, objs, path):
    pattern = ""
    for tuple in nx.utils.pairwise(path):
        a = getObj(tuple[0], objs)
        b = getObj(tuple[1], objs)
        # Stop Node
        if isStop(a):
            pattern += "*"
        # Edge of the Graph
        e = G.get_edge_data(tuple[0], tuple[1])
        e_mot_c = e.get("mot").char()
        pattern += e_mot_c
    return pattern


def should_ignore_path_by_pattern(path_pattern):
    if (
        "F*F" in path_pattern
        or "C*C" in path_pattern
        or "V*V" in path_pattern
        or "S*F" in path_pattern
    ):
        return True
    return False


"""
def create_mot_path_pattern(G, objs, path):
    pattern = ""
    for tuple in nx.utils.pairwise(path):
        a = getObj(tuple[0], objs)
        b = getObj(tuple[1], objs)
        # Edge of the Graph
        e = G.get_edge_data(tuple[0], tuple[1])
        e_mot_c = e.get("mot").char()
        pattern += e_mot_c
    return pattern
"""


def get_scooter_stop_location(points):
    total_distance = 0
    n = len(points)
    for i in range(1, n):
        a = Location.from_list(points[i - 1], reversed=True)
        b = Location.from_list(points[i], reversed=True)
        total_distance += a.distance_to(b)
        if total_distance > MAX_SCOOTER_DISTANCE:
            return a
    return points[n - 1]


def get_close_scooter_from_list(t, scooters):
    t_lat = t[0]
    t_lng = t[1]
    the_scooter = None
    the_distance = sys.float_info.max
    for scooter in scooters:
        distance = scooter.loc.distance_to(Location(lat=t_lat, lng=t_lng))
        if distance < the_distance:
            the_scooter = scooter
            the_distance = distance
    if the_scooter is None:
        raise ValueError(f"Cannot find scooter with the given data t: {t}")
    return the_scooter


DBSCAN_RADIUS = 0.5  # 500 m = 0.5 km


def get_possible_routes(
    objs: List[Union[Point, Vehicle, Stop]],
    weather: WeatherConditions,
    traffic: TrafficConditions,
    escooter_clustering=False,
    exclude_scooters=False,
    exclude_cars=False,
    exclude_sea_vessels=False,
    debug=False,
    geojson=False,
    returnG=False,
) -> pd.DataFrame:
    """Returns a Table with possible multi-modal transportation routes and a few features for each one of them."""

    if debug:
        print("POIs (Points/Vehicles/Stops) Length:", len(objs))
        p, v, s = count_entity_type(objs)
        print(" - Points:   ", p)
        print(" - Vehicles: ", v)
        print(" - Stops:    ", s)
        print("Weather ...", weather)
        print("Traffic ...", traffic)
        print(f" * escooter_clustering: {escooter_clustering}")
        print(f" * exclude_scooters:    {exclude_scooters}")
        print(f" * exclude_cars:        {exclude_cars}")
        print(f" * exclude_sea_vessels: {exclude_sea_vessels}")
        print()

    # Exclude vehicles based on weather conditions (and user preferences)
    eligible_objs = []
    for o in objs:
        if exclude_scooters or (weather is not None and weather.isRaining):
            # Exclude Scooters (and Scooter Stops -  if any)
            if isScooter(o) or isScooterStop(o):
                continue

        if exclude_cars:
            # Exclude Cars and Parking Areas
            if isCar(o) or isCarStop(o):
                continue

        if exclude_sea_vessels or (weather is not None and weather.isWindy):
            # Exclude Sea Vessels and Ports
            if isSeaVessel(o) or isSeaVesselStop(o):
                continue

        eligible_objs.append(o)

    objs = eligible_objs

    # Accelerate process using e-scooter clustering (if being necessary)
    if not exclude_scooters and escooter_clustering:
        # Detect Scooters
        scooters = []
        for o in objs:
            if isScooter(o):
                scooters.append(o)

        # Create a DataFrame with the Lat/Lng of the Scooters
        latlng_tuples = []
        for scooter in scooters:
            latlng_tuples.append((scooter.loc.lat, scooter.loc.lng))
        latlng_df = pd.DataFrame(latlng_tuples, columns=["lat", "lng"])

        # Cluster using DB Scan (with haversine)
        coords = np.radians(latlng_df[["lat", "lng"]])
        db = DBSCAN(eps=DBSCAN_RADIUS / 6371, min_samples=1, metric="haversine")
        latlng_df["cluster"] = db.fit_predict(coords)

        # Find the mean of the centers
        centers = (
            latlng_df[latlng_df["cluster"] != -1]
            .groupby("cluster")[["lat", "lng"]]
            .mean()
            .reset_index()
        )

        # Find the scooters being closer to the means ..:
        selected_scooters = []
        for center in centers.itertuples(index=False):
            close_scooter = get_close_scooter_from_list(
                (center.lat, center.lng), scooters
            )
            selected_scooters.append(close_scooter)

        # Replace ALL scooters with the SELECTED ones
        revised_objs = [o for o in objs if o not in scooters]
        revised_objs.extend(selected_scooters)

        if debug:
            print(
                f"SELECTED e-scooters: {len(selected_scooters)} - Eligible Obj BEFORE: {len(objs)} --> AFTER: {len(revised_objs)}\n"
            )

        objs = revised_objs

    # Visualize ALL Entities
    if geojson:
        visualize_pois(objs, toClipboard=False, toFile="tmp/1a-ALL-nodes.geojson")

    # Create Graph (i.e., Nodes and Links among them) and return both graph and "updated" POIs
    # The POIs are the appropriate ones (i.e., start/end position, e-scooters, parkings plus "a few" cars not in parkings, ports)
    # Nevertheless the links among them have been added based on rough estimations
    G = create_graph(objs, weather)
    if debug:
        print("Graph - number of nodes: ", G.number_of_nodes())
        print("Graph - number_of_edges(): ", G.number_of_edges())

    if geojson:
        visualize_graph(
            objs, G, toClipboard=False, toFile="tmp/1b-Graph-nodes-and-edges.geojson"
        )

    # Find ALL Paths (nevertheless, many of them may not be real ones ...)
    paths = []
    if len(G) > 0:
        paths = list(nx.all_simple_paths(G, source="START", target="END", cutoff=6))
    if debug:
        print("\nNumber of possible routes/paths:", len(paths))

    # Visualize ALL Entities and Links among them, based on the routes/paths found
    if geojson:
        visualize_pois_and_links(
            objs,
            paths,
            G,
            true_paths=False,
            toClipboard=False,
            toFile="tmp/2a-ALL-nodes-and-links.geojson",
        )
        visualize_pois_and_links(
            objs,
            paths,
            G,
            true_paths=True,
            toClipboard=False,
            toFile="tmp/2b-ALL-nodes-and-REAL-paths.geojson",
        )

    # Find the feasible routes/paths and compute a few features for each one of them
    tuple_list = []
    mot_ignore = 0
    constraints_ignore = 0
    scooter_stops_list = []
    tmp_scooter_stop_index = max([o.id for o in objs if isStop(o)])
    for i, path in enumerate(paths, start=1):
        n = len(list(path)) - 1

        if debug:
            print(f"Path {i:3}: [{n}] {path}", end="")

        pattern = create_path_pattern(G, objs, path)
        if should_ignore_path_by_pattern(pattern):
            if debug:
                print(f" - pattern: {pattern} - Route ignored !")
            mot_ignore += 1
            continue

        # # Check Means of Transport used for inappropriate cases (e.g., walk to port but not using a sea-vessel but walk again)
        # pattern = create_mot_path_pattern(G, objs, path)
        # if "FF" in pattern or "BB" in pattern or "CC" in pattern or "SS" in pattern or "SFS" in pattern or "CFC" in pattern:
        #     if debug: print(f" - pattern: {pattern} - Route ignored !")
        #     mot_ignore += 1
        #     continue

        # TODO: Compute more features including but not limited to
        # Energy Consumption and CO2 (eco) footprint

        new_path = path

        walk_count = walk_distance = 0
        car_count = car_distance = 0
        escooter_count = escooter_distance = 0
        sea_vessel_count = sea_vessel_distance = 0
        total_cost = total_dist = total_dur = 0
        expected_intermediate_time = [0]
        for tuple in nx.utils.pairwise(path):
            a = getObj(tuple[0], objs)
            b = getObj(tuple[1], objs)

            # Edge of the Graph
            e = G.get_edge_data(tuple[0], tuple[1])
            e_mot = e.get("mot")
            e_cost = e.get("cost")

            # Interaction with Open Street Map Service (directions - driving-car / foot-walking / cycling-electric)
            # for expected route and hence distance and duration
            r = getTransData(a.loc, b.loc, e_mot)
            ignore_route = False
            try:
                # Expected Distance and Duration
                path_distance = r[0]["distance"]
                path_dur = r[0]["duration"]

                # Ensure that relevant constraints are satisfied
                if e_mot == TransportType.FOOT and path_distance > MAX_WALK_DISTANCE:
                    if debug:
                        print(
                            f" - {a.uid()}-{b.uid()} - path_distance: {path_distance} > MAX_WALK_DISTANCE - Route ignored !"
                        )
                    ignore_route = True
                    break
                elif e_mot == TransportType.CAR and path_distance > MAX_CAR_DISTANCE:
                    if debug:
                        print(
                            f" - {a.uid()}-{b.uid()} - path_distance: {path_distance} > MAX_SCOOTER_DISTANCE - Route ignored !"
                        )
                    ignore_route = True
                    break
                elif e_mot == TransportType.SCOOTER and path_distance > (
                    MAX_SCOOTER_DISTANCE + MAX_WALK_DISTANCE
                ):
                    if debug:
                        print(
                            f" - {a.uid()}-{b.uid()} - path_distance: {path_distance} > MAX_SCOOTER_DISTANCE - Route ignored !"
                        )
                    ignore_route = True
                    break

                if e_mot == TransportType.FOOT:
                    walk_count += 1
                    walk_distance += path_distance
                    expected_intermediate_time.append(total_dur + path_dur)
                elif e_mot == TransportType.CAR:
                    car_count += 1
                    car_distance += path_distance
                    expected_intermediate_time.append(total_dur + path_dur)
                elif e_mot == TransportType.SCOOTER:
                    if path_distance <= MAX_SCOOTER_DISTANCE:
                        escooter_count += 1
                        escooter_distance += path_distance
                        expected_intermediate_time.append(total_dur + path_dur)
                    else:
                        # Leave the scooter just before we exceed max scooter distance
                        scooter_stop_location = get_scooter_stop_location(r[1])
                        tmp_scooter_stop_index += 1
                        scooter_stop = Stop(
                            id=tmp_scooter_stop_index,
                            name="tmp",
                            type=StopType.SCOOTER_STOP,
                            loc=scooter_stop_location,
                        )

                        # G.remove_edge(a.uid(), b.uid()) # Not remove since it may used by another path
                        G.add_edge(
                            a.uid(),
                            scooter_stop.uid(),
                            cost=SCOOTER_RENT_COST,
                            mot=TransportType.SCOOTER,
                        )
                        G.add_edge(
                            scooter_stop.uid(),
                            b.uid(),
                            cost=WALK_COST,
                            mot=TransportType.FOOT,
                        )

                        objs.append(scooter_stop)
                        scooter_stops_list.append(scooter_stop)

                        if debug:
                            print(
                                " * Leave scooter at:",
                                scooter_stop.loc,
                                " (path & pattern revised)",
                                end="",
                            )
                        # Part 1 .. by scooter
                        ra = getTransData(
                            a.loc, scooter_stop_location, TransportType.SCOOTER
                        )
                        a_path_distance = ra[0]["distance"]
                        a_path_dur = ra[0]["duration"]
                        escooter_count += 1
                        escooter_distance += a_path_distance
                        # Part 2 .. by foot
                        rb = getTransData(
                            scooter_stop_location, b.loc, TransportType.FOOT
                        )
                        b_path_distance = rb[0]["distance"]
                        b_path_dur = rb[0]["duration"]
                        walk_count += 1
                        walk_distance += b_path_distance
                        # Revise Path and Pattern, Distance and Duration
                        path_distance = a_path_distance + b_path_distance
                        path_dur = a_path_dur + b_path_dur

                        new_path = []
                        index = None
                        for i, element in enumerate(path):
                            new_path.append(element)
                            if element == a.uid():
                                index = i + 1
                                new_path.append(scooter_stop.uid())
                        pattern = (
                            create_path_pattern(G, objs, path[:index])
                            + "SF"
                            + create_path_pattern(G, objs, path[index : len(path)])
                        )
                        if should_ignore_path_by_pattern(pattern):
                            if debug:
                                print(f" - pattern: {pattern} - Route ignored !")
                            # mot_ignore += 1
                            ignore_route = True
                            break
                        expected_intermediate_time.append(total_dur + a_path_dur)
                        expected_intermediate_time.append(
                            total_dur + a_path_dur + b_path_dur
                        )
                elif e_mot == TransportType.SEA_VESSEL:
                    sea_vessel_count += 1
                    sea_vessel_distance += path_distance
                    expected_intermediate_time.append(total_dur + path_dur)

                total_dist += path_distance
                total_dur += path_dur

                # About Traffic ... affects cars/busses ... increase duration proportionally
                traffic_jams = 0
                if e_mot == TransportType.CAR or e_mot == TransportType.BUS:
                    for traffic_location in traffic.highTrafficLocations:
                        if path_approaches_location(
                            r[1], (traffic_location.lng, traffic_location.lat), 10
                        ):
                            traffic_jams = traffic_jams + 1
                if traffic_jams > 0:
                    total_dur = total_dur + traffic_jams * AVG_TRAFFIC_JAM_DELAY

                # About Parking ...
                if isCar(a):
                    # total_dist = total_dist + AVG_CAR_PARKING_DISTANCE # or check if destination is parking location or not ...
                    total_dur = total_dur + AVG_CAR_PARKING_DURATION

                # Cost
                total_cost = total_cost + e_cost

            except Exception as e:
                ignore_route = True
                break

        if ignore_route:
            constraints_ignore += 1
            continue

        if debug:
            print(
                " -- total_dist:",
                total_dist,
                ", total_dur:",
                total_dur,
                ", total_cost:",
                total_cost,
            )

        tuple_list.append(
            (
                new_path,
                pattern,
                n,
                total_dist,
                total_dur,
                total_cost,
                walk_count,
                walk_distance,
                car_count,
                car_distance,
                escooter_count,
                escooter_distance,
                sea_vessel_count,
                sea_vessel_distance,
                expected_intermediate_time,
            )
        )

    if debug:
        print("\nNumber of feasible routes/paths:", len(tuple_list))
        print(" ... ignored due to invalid MoT:", mot_ignore)
        print(" ... ignored due to constraint violation:", constraints_ignore)

    if geojson:
        revised_paths = []
        for t in tuple_list:
            revised_paths.append(t[0])
        visualize_pois_and_links(
            objs,
            revised_paths,
            G,
            true_paths=False,
            toClipboard=False,
            toFile="tmp/3a-ALL-nodes-and-SELECTED-links.geojson",
        )
        visualize_pois_and_links(
            objs,
            revised_paths,
            G,
            true_paths=True,
            toClipboard=False,
            toFile="tmp/3b-ALL-nodes-and-SELECTED-REAL-paths.geojson",
        )

    # Create and Return a DataFrame with all possible paths and features computed for each one of them
    tuple_list_columns = [
        "path",
        "pattern",
        "edges",
        "total_distance",
        "total_duration",
        "total_cost",
        "walk_count",
        "walk_distance",
        "car_count",
        "car_distance",
        "escooter_count",
        "escooter_distance",
        "sea_vessel_count",
        "sea_vessel_distance",
        "expected_intermediate_time",
    ]
    df = pd.DataFrame(tuple_list, columns=tuple_list_columns)

    if debug:
        print(df)

    # Find and Vizualize Top Routes per category (i.e., core feature) ...
    if geojson:
        if df.empty:
            print("\n *** No available path found !!! ***\n")
        else:
            # Find and Show the best paths by category/column
            min_distance_path = df.loc[df["total_distance"].idxmin()].path
            min_duration_path = df.loc[df["total_duration"].idxmin()].path
            min_cost_path = df.loc[df["total_cost"].idxmin()].path
            min_edges_path = df.loc[df["edges"].idxmin()].path

            print("\nBrief Analysis ... before returning DataFrame")
            print(" - MIN distance:", min_distance_path)
            print(" - MIN duration:", min_duration_path)
            print(" - MIN cost:    ", min_cost_path)
            print(" - MIN edges: ", min_edges_path)

            selected_paths_list = [
                min_distance_path,
                min_duration_path,
                min_cost_path,
                min_edges_path,
            ]
            visualize_pois_and_links(
                objs,
                selected_paths_list,
                G,
                true_paths=True,
                toClipboard=False,
                toFile="tmp/4-the-selected.geojson",
            )

    if returnG:
        return (df, scooter_stops_list, G)
    else:
        return (df, scooter_stops_list)


# Serializable File with Testing Data
TEST_FILE_PATH_1 = "tmp-history/test/subset_pois-data-2025-12-28--02-43-01.pkl"
TEST_FILE_PATH_2 = "tmp-history/test/pois-data-2025-12-28--01-06-56.pkl"
TEST_FILE_PATH_3 = "tmp-history/test/pois-data-2025-12-30--01-11-43.pkl"

# Start and End Locations
USER_START_LOCATION = Location(41.0417, 28.9882)
USER_END_LOCATION = Location(lat=41.008583, lng=28.980175)

CASE_31_USER_START_LOCATION = Location(lat=41.067256, lng=29.018705)
CASE_31_USER_END_LOCATION = Location(lat=41.01730014372967, lng=28.96863342339102)

CASE_32_USER_START_LOCATION = Location(lat=41.009477, lng=28.977335)
CASE_32_USER_END_LOCATION = Location(lat=41.0485255426439, lng=28.933688939004377)

# Weather
GOOD_WEATHER_CONDITIONS = WeatherConditions(isRaining=False, isWindy=False)
RAINING_DAY_WEATHER_CONDITIONS = WeatherConditions(isRaining=True, isWindy=False)
WINDY_DAY_WEATHER_CONDITIONS = WeatherConditions(isRaining=False, isWindy=True)
BAD_WEATHER_CONDITIONS = WeatherConditions(isRaining=True, isWindy=True)

# Traffic
NO_TRAFFIC = TrafficConditions([])
GALATA_BRIDGE_JAM = TrafficConditions(
    [Location(lat=41.02036910180452, lng=28.973383541007976)]
)  # Galata Bridge
ATATURK_BRIDGE_JAM = TrafficConditions(
    [Location(lat=41.024268, lng=28.965210)]
)  # Ataturk Bridge
# TrafficConditions([Location(lat=41.02036910180452, lng=28.973383541007976)]) # Galata Bridge
# TrafficConditions([Location(lat=41.024268, lng=28.965210)]) # Ataturk Bridge

# Debugging Flags
PRINT_FLAG = True
GEOJSON_FLAG = True

if __name__ == "__main__":
    print("\nRoute Planning Algorithm Testing\n")

    # >> INPUT DATA
    # Load testing data (vehicles and stops from a ser file, and then add start & stop (aka origin and destination) locations)
    path = TEST_FILE_PATH_3
    with open(path, "rb") as f:
        the_pois = pickle.load(f)
    # Patch
    for poi in the_pois:
        if isScooter(poi) and poi.id == 1:
            poi.set_location(Location(41.03730500954889, 28.986508383123162))
        if isCar(poi) and poi.id == 4:
            poi.set_location(Location(41.03068301297076, 28.978866334511714))
    the_pois.append(
        Vehicle(
            7, TransportType.SCOOTER, Location(41.02650174881941, 28.97313496050368)
        )
    )

    # Add Start and End points
    start_end_points = [
        # Point("START", USER_START_LOCATION ), Point("END", USER_END_LOCATION)
        # Point("START", USER_END_LOCATION ), Point("END", USER_START_LOCATION)
        Point("START", CASE_32_USER_START_LOCATION),
        Point("END", CASE_32_USER_END_LOCATION),
    ]
    # Create a List with POIs (i.e., Points, Vehicles and Stops)
    objs = the_pois + start_end_points

    # TODO: Uncomment ... for the Example documented
    from sample_data_v2 import *

    objs = get_pois()

    # Weather and Traffic Conditions
    weathe_conditions = GOOD_WEATHER_CONDITIONS
    traffic_conditions = NO_TRAFFIC

    time_start = time.perf_counter()

    # >> FIND POSSIBLE ROUTES
    df, ss_list = get_possible_routes(
        objs,
        weather=weathe_conditions,
        traffic=traffic_conditions,
        escooter_clustering=True,
        debug=PRINT_FLAG,
        geojson=GEOJSON_FLAG,
    )

    print(f"new stops: {len(ss_list)}")

    time_elapsed = time.perf_counter() - time_start
    print(f"\nElapsed time: {time_elapsed:.4f} seconds")

    if True:
        print("Feasible Routes - distances in meters, durations in minutes")
        tmp_df = df.copy()
        tmp_df["total_duration"] = tmp_df["total_duration"] / 60
        print(
            df[
                [
                    "path",
                    "pattern",
                    "total_distance",
                    "total_duration",
                    "walk_distance",
                    "car_distance",
                    "escooter_distance",
                ]
            ]
        )
