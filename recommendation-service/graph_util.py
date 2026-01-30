# ----------------------------------------------------------------------------------------
# Help Construct Graph for Route Planning purposes
# ----------------------------------------------------------------------------------------

# Note: Here we cover the second Layer i.e., Graph Construction for detecting possible routes

from typing import List
import networkx as nx
from .config import *
from .data_structures import *

# Helper Functions


def existsSeaVessel(a, os):
    for o in os:
        if isSeaVessel(o) and a.loc.distance_to(o.loc) < MAX_DISTANCE_FROM_STOP:
            return True
    return False


def existsCar(a, os):
    for o in os:
        if isCar(o) and a.loc.distance_to(o.loc) < MAX_DISTANCE_FROM_STOP:
            return True
    return False


def isVehicleToStop(a, os):
    if isCarStop(a) and existsCar(a, os):
        return True
    if isSeaVesselStop(a) and existsSeaVessel(a, os):
        return True
    return False


def existsInCarStop(car, car_stops):
    for cp in car_stops:
        if cp.loc.distance_to(car.loc) < MAX_DISTANCE_FROM_STOP:
            return True
    return False


# Error Factor ...
FACTOR = 1.2

# Main Algorithm


def create_graph(objs: List, weather: WeatherConditions):
    # Check if we can possibly link start and end points with the rest ones

    start_point = end_point = None
    for o in objs:
        if start_point is None and isStartPoint(o):
            start_point = o
        if end_point is None and isEndPoint(o):
            end_point = o

    if start_point is None or end_point is None:
        # print(" *** No start/end point ***")
        return nx.DiGraph()

    start_link_feasible = end_link_feasible = False
    for o in objs:
        if o == start_point or o == end_point:
            continue
        if not start_link_feasible:
            start_dist = start_point.loc.distance_to(o.loc)
            if start_dist <= MAX_WALK_DISTANCE:
                start_link_feasible = True
        if not end_link_feasible:
            end_dist = end_point.loc.distance_to(o.loc)
            if isCarStop(o) and end_dist <= MAX_WALK_DISTANCE:
                end_link_feasible = True
            if isScooter(o) and end_dist <= (MAX_SCOOTER_DISTANCE + MAX_WALK_DISTANCE):
                end_link_feasible = True
            if isSeaVesselStop(o) and end_dist <= MAX_WALK_DISTANCE:
                end_link_feasible = True

    if not start_link_feasible or not end_link_feasible:
        # print(" *** No start/end point link ***")
        return nx.DiGraph()

    # Detect parkings
    car_stops = set({})
    for obj in objs:
        if isCarStop(obj):
            car_stops.add(obj)

    # Detect the points of interest (pois)
    # pois: Points, escooters and cars (out of parking), stops (including parkings and ports)
    # others: Cars (in parkings), Buses and Sea Vessels
    pois, others = [], []
    for obj in objs:
        if isBus(obj) or isSeaVessel(obj):
            others.append(obj)
        elif isCar(obj) and existsInCarStop(obj, car_stops):
            others.append(obj)
        else:
            pois.append(obj)

    # Create Graph
    G = nx.DiGraph()
    # Add Edges -  When adding an Edge the relevant nodes are automatically included in the Graph
    n = len(pois)
    for i in range(0, n):
        for j in range(0, n):
            if i == j:
                continue

            # Temp Origin and Destination
            a = pois[i]
            b = pois[j]

            # Distances ...
            line_dist = a.loc.distance_to(b.loc)
            # For accerating the graph construction process, we can assume that
            # the real distance is a bit higher than the straight-line distance
            walk_dist = FACTOR * line_dist
            scooter_dist = FACTOR * line_dist
            car_dist = FACTOR * line_dist

            # Walking ... Getting another means of Transport
            if (isStartPoint(a) or isStop(a)) and walk_dist <= MAX_WALK_DISTANCE:
                can_walk = True
                if isSeaVesselStop(a) and isSeaVesselStop(b):
                    can_walk = False
                if isCarStop(a) and isCarStop(b):
                    next_flag = False
                if can_walk:
                    G.add_edge(a.uid(), b.uid(), cost=WALK_COST, mot=TransportType.FOOT)
                    # print("WALK... ", a.uid(), b.uid(), "\t", a.loc, b.loc)

            # Scooters and Cars (out of parking areas)
            if isVehicle(a):
                if (
                    not weather.isRaining
                    and isScooter(a)
                    and (
                        isCar(b)
                        or (isStop(b) and isVehicleToStop(b, others))
                        or isEndPoint(b)
                    )
                ):
                    if scooter_dist <= (MAX_SCOOTER_DISTANCE + MAX_WALK_DISTANCE):
                        # print("SCOOTER... ", a.uid(), b.uid(), " - scooter_dist:", scooter_dist)
                        G.add_edge(
                            a.uid(),
                            b.uid(),
                            cost=SCOOTER_RENT_COST,
                            mot=TransportType.SCOOTER,
                        )

                if isCar(a) and isCarStop(b) and car_dist <= MAX_CAR_DISTANCE:
                    # print("* CAR... ", a.uid(), b.uid())
                    G.add_edge(
                        a.uid(), b.uid(), cost=CAR_RENT_COST, mot=TransportType.CAR
                    )

            # Cars (in parking areas) and Sea Vessels
            if isStop(a) and isStop(b):
                if isCarStop(a) and isCarStop(b) and existsCar(a, others):
                    # print("CAR... ", a.uid(), b.uid())
                    G.add_edge(
                        a.uid(), b.uid(), cost=CAR_RENT_COST, mot=TransportType.CAR
                    )

                # In case of a bus .. stop .. we should check if there is a line/path connecting these stops
                # in this case .. we should provide the duration should be the average/expected .. for bus line..

                if (
                    not weather.isWindy
                    and isSeaVesselStop(a)
                    and isSeaVesselStop(b)
                    and existsSeaVessel(a, others)
                ):
                    # print("SEA... ", a.uid(), b.uid())
                    G.add_edge(
                        a.uid(),
                        b.uid(),
                        cost=SEA_VESSEL_TRIP_COST,
                        mot=TransportType.SEA_VESSEL,
                    )

    return G
