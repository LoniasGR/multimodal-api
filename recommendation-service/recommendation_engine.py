from typing import List
import time
import pickle
import pandas as pd
from data_structures import isCar, isScooter, Location, Point
from route_planning import *
from dataclasses import dataclass

"""
# Serializable File with Testing Data
TEST_FILE_PATH_1 = "test/subset_pois-data-2025-12-28--02-43-01.pkl"
TEST_FILE_PATH_2 = "test/pois-data-2025-12-28--01-06-56.pkl"

# Start and End Locations
USER_START_LOCATION = Location(41.0417, 28.9882)
USER_END_LOCATION = Location(lat=41.008583, lng=28.980175)

# Weather 
GOOD_WEATHER_CONDITIONS = WeatherConditions(isRaining=False, isWindy=False)
RAINING_DAY_WEATHER_CONDITIONS = WeatherConditions(isRaining=True, isWindy=False)
WINDY_DAY_WEATHER_CONDITIONS = WeatherConditions(isRaining=False, isWindy=True)
BAD_WEATHER_CONDITIONS = WeatherConditions(isRaining=True, isWindy=True)

# Traffic
NO_TRAFFIC = TrafficConditions([]) 
GALATA_BRIDGE_JAM = TrafficConditions([Location(lat=41.02036910180452, lng=28.973383541007976)]) # Galata Bridge
ATATURK_BRIDGE_JAM =TrafficConditions([Location(lat=41.024268, lng=28.965210)]) # Ataturk Bridge
        # TrafficConditions([Location(lat=41.02036910180452, lng=28.973383541007976)]) # Galata Bridge
        # TrafficConditions([Location(lat=41.024268, lng=28.965210)]) # Ataturk Bridge
"""

# Debugging Flags
PRINT_FLAG = False  # True
GEOJSON_FLAG = False  # True

ALLOWED_FEATURES = set(
    {
        "edges",
        # 'pattern',
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
    }
)

ALLOWED_MEANS_OF_TRANSPORT = set({"walk", "car", "escooter", "sea_vessel"})


@dataclass
class UserPreference:
    features: List[str]
    avoids: List[str]

    def __post_init__(self):
        invalid_features = set(self.features) - ALLOWED_FEATURES
        if invalid_features:
            raise ValueError(f"Invalid feature values: {invalid_features}")
        invalid_avoids = set(self.avoids) - ALLOWED_MEANS_OF_TRANSPORT
        if invalid_avoids:
            raise ValueError(
                f"Invalid avoid (means of transport) values: {invalid_avoids}"
            )

    def __str__(self) -> str:
        return f"UserPreference(features={self.features}, avoids={self.avoids})"


USER_PREF_AVOID_SCOOTERS = UserPreference(
    features=["walk_distance"], avoids=["escooter"]
)
USER_PREF_AVOID_CARS = UserPreference(features=["total_duration"], avoids=["car"])
USER_PREF_OTHER = UserPreference(
    features=["total_duration", "total_cost", "walk_distance"], avoids=["sea_vessel"]
)


def user_preference_to_boolean_flags(user_preference: UserPreference):
    avoid_cars = avoid_scooters = avoid_sea_vessels = False
    if user_preference is not None and user_preference.avoids:
        if "car" in user_preference.avoids:
            avoid_cars = True
        if "escooter" in user_preference.avoids:
            avoid_scooters = True
        if "sea_vessel" in user_preference.avoids:
            avoid_sea_vessels = True
    return (avoid_cars, avoid_scooters, avoid_sea_vessels)


def filter_order_routes(
    df: pd.DataFrame,
    temp_data: TempData,
    user: User,
    user_preferences: UserPreference,
    ml_model,
) -> pd.DataFrame:
    if df.empty:
        return df

    # User Preferences (Features Order, Vehicle Restrictions)
    if user_preferences is not None:
        # Filter data based on constraints (i.e., avoids) specified
        filtered_df = df
        if user_preferences.avoids:
            mask = pd.Series(True, index=df.index)
            # Update Mask based on constraints (i.e., avoids) specified
            for mot in user_preferences.avoids:
                df_feature = mot + "_count"
                mask &= df[df_feature] == 0
            # Filter Data
            filtered_df = df.loc[mask]

        # Sort filtered data based on features provided (in an ascending order)
        sorted_filtered_df = filtered_df
        if user_preferences.features:
            sorted_filtered_df = filtered_df.sort_values(
                by=user_preferences.features, ascending=True
            )

        return sorted_filtered_df.reset_index(drop=True)

    # ML model-driven Route Assessment/Ordering
    if ml_model is not None:
        print("\n** ml_model\n")
        ml_sorted_df = df
        temp_data_features = (temp_data.day_of_week, temp_data.hour_of_day)
        user_demo_features = (user.sex, user.age_group)

        # TODO: update
        # Find Features: Date/Time - User Demographics, Subset of Route Features, etc.
        # Use ML model for ranking ... add feature to DF and order by this feature
        # Note: We can possibly have ML model per user, depending on the data available for each one of them

        return ml_sorted_df

    return df.sort_values(by="total_duration", ascending=True).reset_index(drop=True)


if __name__ == "__main__":
    print("Recommendation Engine Algorithm Testing")

    # >> INPUT DATA (1) for FINDING POSSIBLE ROUTES

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
    # Add Start and End points
    start_end_points = [
        # Point("START", USER_START_LOCATION ),  Point("END", USER_END_LOCATION)
        Point("START", CASE_32_USER_START_LOCATION),
        Point("END", CASE_32_USER_END_LOCATION),
    ]
    # Create a List with POIs (i.e., Points, Vehicles and Stops)
    objs = the_pois + start_end_points

    # Weather and Traffic Conditions
    weathe_conditions = GOOD_WEATHER_CONDITIONS
    traffic_conditions = NO_TRAFFIC

    time_start = time.perf_counter()

    # User
    user = User(1, SexValue.MALE, AgeGroupValue.CHILD)

    # User Preferences
    user_preferences = USER_PREF_AVOID_CARS

    # Check if we should avoid specific means of transportation
    avoid_cars, avoid_scooters, avoid_sea_vessels = user_preference_to_boolean_flags(
        user_preferences
    )

    # >> FIND POSSIBLE ROUTES
    df, _ = get_possible_routes(
        objs,
        weather=weathe_conditions,
        traffic=traffic_conditions,
        escooter_clustering=True,
        exclude_cars=avoid_cars,
        exclude_scooters=avoid_scooters,
        exclude_sea_vessels=avoid_sea_vessels,
        debug=False,
        geojson=False,
    )

    print(df)
    print(df.columns.tolist())

    # >> INPUT DATA (2)  FOR GETTING RECOMMENDATIONS (optional)

    # Date and Time
    td = TempData.from_datetime(datetime.now())

    # TODO: ML Model (Load from File, if available)
    ml_model = None

    # >> FILTER AND SORT FEASIBLE ROUTES
    new_df = filter_order_routes(
        df, td, user, user_preferences=user_preferences, ml_model=ml_model
    )

    user_preferences_features = []
    if user_preferences and user_preferences.features:
        user_preferences_features = user_preferences.features
    avoid_features = []
    if user_preferences and user_preferences.avoids:
        avoid_features = [a + "_count" for a in user_preferences.avoids]
    new_df_features = ["path", "pattern"] + user_preferences_features + avoid_features
    print("\nSorted...")
    print(new_df[new_df_features])

    time_elapsed = time.perf_counter() - time_start
    print(f"\nElapsed time: {time_elapsed:.4f} seconds")

    selected_row = new_df.iloc[0]
    print(
        f"selected route: {selected_row.path} - pattern: {selected_row.pattern} - total_duration: {selected_row.total_duration / 60} mins"
    )

    """
    def get_vehicle_in_stop(s, objs):
        for obj in objs:
            if isCarStop(s) and isCar(obj) and s.loc.distance_to(obj.loc) < MAX_DISTANCE_FROM_STOP:
                return obj
            if isSeaVesselStop(s) and isSeaVessel(obj) and s.loc.distance_to(obj.loc) < MAX_DISTANCE_FROM_STOP:
                return obj
        return None

    print(selected_row.path)
    print(selected_row.expected_intermediate_time)
    for i, id in enumerate(selected_row.path):
        print(id)
        obj = getObj(id, objs)
        if obj is not None: 
            if isVehicle(obj):
                print(" - Vehicle: ", obj, ", Expected:", selected_row.expected_intermediate_time[i])
            if isStop(obj) and not isStop(prev_obj):
                v_obj = get_vehicle_in_stop(obj, objs)
                print(" * Vehicle: ", v_obj, ", Expected:", selected_row.expected_intermediate_time[i])
        prev_obj = obj
                # print(" - isVehicle:", isVehicle(obj), ", isStop:", isStop(obj))
    """

    # Testing ML Model
    ml_model_path = "test/ml-model.pkl"
    print("Load Model from File... ", ml_model_path)
    with open(ml_model_path, "rb") as f:
        model = pickle.load(f)

    # Use ML Model for getting recommendations ...
    tmp_df = df.copy()
    tmp_df_path = tmp_df.path
    # Add User Demographics - Using one-hot-encoding
    tmp_df["age_group_child"] = user.age_group == AgeGroupValue.CHILD
    tmp_df["age_group_adult"] = user.age_group == AgeGroupValue.ADULT
    tmp_df["age_group_senior"] = user.age_group == AgeGroupValue.SENIOR
    tmp_df["sex_male"] = user.sex == SexValue.MALE
    tmp_df["sex_female"] = user.sex == SexValue.FEMALE
    tmp_df = tmp_df.drop(columns=["path", "pattern", "expected_intermediate_time"])
    # Predict category and probability (of 1) using ML model
    routes_predictions_category = model.predict(tmp_df)
    routes_predictions_proba_1 = model.predict_proba(tmp_df)[:, 1]
    tmp_df.loc[tmp_df.index, "predicted_category"] = routes_predictions_category
    tmp_df.loc[tmp_df.index, "probability_is_one"] = routes_predictions_proba_1
    tmp_df.loc[tmp_df.index, "path"] = tmp_df_path
    # Sort and Select
    sorted = tmp_df.sort_values(by="probability_is_one", ascending=False).reset_index(
        drop=True
    )
    ml_selected_route = sorted.iloc[0].path
    print("ML selected route:", ml_selected_route)
