from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pandas import DataFrame

from .data_structures import (
    Location,
    Point,
    Stop,
    TrafficConditions,
    Vehicle,
    WeatherConditions,
    TempData,
)
from .route_planning import get_possible_routes
from .recommendation_engine import UserPreference, filter_order_routes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendationRequest:
    avoid_cars: bool
    avoid_scooters: bool
    avoid_sea_vessels: bool
    vehicles: list[Vehicle]
    stops: list[Stop]
    origin: Location
    destination: Location
    minimizing_value: str


@app.post("/suggest", response_model=None)
def create_suggestion(rr: RecommendationRequest):
    weather_conditions = WeatherConditions(isRaining=False, isWindy=False)
    traffic_conditions = TrafficConditions([])
    start = Point("START", loc=rr.origin)
    end = Point("END", loc=rr.destination)

    objs = [start, end] + rr.vehicles + rr.stops

    df = get_possible_routes(
        objs,
        weather=weather_conditions,
        traffic=traffic_conditions,
        escooter_clustering=True,
        exclude_cars=rr.avoid_cars,
        exclude_scooters=rr.avoid_scooters,
        exclude_sea_vessels=rr.avoid_sea_vessels,
        debug=False,
        geojson=False,
        returnG=True,
    )
    avoids = []
    if rr.avoid_cars:
        avoids.append("car")
    if rr.avoid_scooters:
        avoids.append("scooter")
    if rr.avoid_sea_vessels:
        avoids.append("sea_vessel")
    user_preferences = UserPreference(features=[rr.minimizing_value], avoids=avoids)

    # Recommendation Engine - Sort Feasible Routes
    td = TempData.from_datetime(datetime.now())
    new_df = filter_order_routes(
        df, td, user, user_preferences=user_preferences, ml_model=None
    )
