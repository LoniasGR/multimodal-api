from datetime import datetime
from enum import StrEnum

from pydantic import computed_field
from sqlmodel import Field, Relationship, SQLModel

from .location import Location
from .user import User


class RecommendationMode(StrEnum):
    edges = "edges"
    total_distance = "total_distance"
    Total_Duration = "total_duration"
    Total_Cost = "total_cost"
    Walk_Count = "walk_count"
    Walk_Distance = "walk_distance"
    Car_Count = "car_count"
    Car_Distance = "car_distance"
    Escooter_Count = "escooter_count"
    Escooter_Distance = "escooter_distance"
    Sea_Vessel_Count = "se_vessel_count"
    Sea_Vessel_Distance = "se_vessel_distance"


class RecommendationRequestBase(SQLModel):
    mode: RecommendationMode
    walk: bool
    car: bool
    escooter: bool
    sea_vessel: bool


class RecommendationRequestCreate(RecommendationRequestBase):
    origin: Location
    destination: Location


class RecommendationRequest(RecommendationRequestBase, table=True):
    origin_lat: float | None = Field(default=None, exclude=True)
    origin_lng: float | None = Field(default=None, exclude=True)
    destination_lat: float | None = Field(default=None, exclude=True)
    destination_lng: float | None = Field(default=None, exclude=True)
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.name")
    user: User = Relationship()
    date_requested: datetime = Field(default_factory=datetime.now)


class RecommendationRequestPublic(RecommendationRequestBase):
    user: User | None = None
