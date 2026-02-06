from datetime import datetime

from .data_structures import (
    AgeGroupValue,
    SexValue,
    TempData,
    TrafficConditions,
    User,
    WeatherConditions,
)
from .recommendation_engine import (
    UserPreference,
    filter_order_routes,
    user_preference_to_boolean_flags,
)
from .route_planning import get_possible_routes, visualize_pois_and_links
from .sample_data_v2 import get_pois

if __name__ == "__main__":
    print("Testing ...")

    # User (already registered and signed in to the system)
    user = User(1, SexValue.MALE, AgeGroupValue.ADULT)

    # System Current Status - Vehicles, Stops and Start-End Points (read from DB / maintain current status in memory)
    objs = get_pois()

    # User Preferences provided by the GUI
    user_preferences = UserPreference(features=["total_duration"], avoids=["car"])

    # Weather Conditions and Traffic (read from DB)
    weathe_conditions = WeatherConditions(isRaining=False, isWindy=False)
    traffic_conditions = TrafficConditions([])

    # Route Planning - Find Feasible Routes
    avoid_cars, avoid_scooters, avoid_sea_vessels = user_preference_to_boolean_flags(
        user_preferences
    )
    df, ss_list, G = get_possible_routes(
        objs,
        weather=weathe_conditions,
        traffic=traffic_conditions,
        escooter_clustering=True,
        exclude_cars=avoid_cars,
        exclude_scooters=avoid_scooters,
        exclude_sea_vessels=avoid_sea_vessels,
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

    # Output
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
    toClipboard = True  # For testing purposes
    geojson = visualize_pois_and_links(
        objs,
        [selected_row.path],
        G,
        true_paths=True,
        toClipboard=toClipboard,
        toReturn=True,
    )
    print(" ** GEOJSON Length::", len(geojson))
