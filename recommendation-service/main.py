from datetime import datetime
from pandas import DataFrame
from sqlmodel import select, SQLModel

from .db import SessionDep, StopDB, UserDB, VehicleDB
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .data_structures import (
    Location,
    Point,
    Stop,
    TrafficConditions,
    Vehicle,
    WeatherConditions,
    TempData,
)
from .route_planning import get_possible_routes, visualize_pois_and_links
from .recommendation_engine import UserPreference, filter_order_routes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendationRequest(SQLModel):
    username: str
    avoid_cars: bool
    avoid_scooters: bool
    avoid_sea_vessels: bool
    origin: Location
    destination: Location
    minimizing_value: str


@app.post("/suggest", response_model=dict)
def create_suggestion(rr: RecommendationRequest, session: SessionDep):
    weather_conditions = WeatherConditions(isRaining=False, isWindy=False)
    traffic_conditions = TrafficConditions([])
    start = Point("START", loc=rr.origin)
    end = Point("END", loc=rr.destination)

    db_vehicles = session.exec(select(VehicleDB)).all()
    vehicles: list[Vehicle] = [db_vehicle.to_vehicle() for db_vehicle in db_vehicles]

    db_stops = session.exec(select(StopDB)).all()
    stops: list[Stop] = [s.to_stop() for s in db_stops]

    db_user = session.exec(select(UserDB).where(UserDB.username == rr.username)).first()
    if db_user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User information is incorrect")
    user = db_user.to_user()

    objs = [start, end] + vehicles + stops

    avoids = []
    if rr.avoid_cars:
        avoids.append("car")
    if rr.avoid_scooters:
        avoids.append("scooter")
    if rr.avoid_sea_vessels:
        avoids.append("sea_vessel")
    user_preferences = UserPreference(features=[rr.minimizing_value], avoids=avoids)

    df, ss_list, G = get_possible_routes(
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
    print(df)

    # Recommendation Engine - Sort Feasible Routes
    td = TempData.from_datetime(datetime.now())
    new_df = filter_order_routes(
        df, td, user, user_preferences=user_preferences, ml_model=None
    )
    tmp_df = new_df.copy()
    tmp_df["total_duration"] = tmp_df["total_duration"] / 60
    print(
        tmp_df[
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

    # Suggested Path
    selected_row = tmp_df.iloc[0]
    print(
        f"\n ** Suggested Route: {selected_row.path} - pattern: {selected_row.pattern} - total_duration: {selected_row.total_duration} mins"
    )
    # Suggested Path Vizualization (geojson)
    objs.extend(ss_list)
    geojson = visualize_pois_and_links(
        objs,
        [selected_row.path],
        G,
        true_paths=True,
        toClipboard=False,
        toReturn=True,
    )
    import json

    return json.loads(geojson)
