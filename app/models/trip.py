from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from .trip_vehicle import TripVehiclePublicWithVehicle

if TYPE_CHECKING:
    from .trip_vehicle import TripVehicle


class TripBase(SQLModel):
    start_time: datetime
    end_time: datetime
    environmental_conditions: str | None = Field(default=None)
    recommendation_request_id: int = Field(foreign_key="recommendationrequest.id")


class TripCreate(TripBase):
    pass


class Trip(TripBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    vehicles: list["TripVehicle"] = Relationship(back_populates="trip")


class TripPublicWithVehicles(TripBase):
    vehicles: list[TripVehiclePublicWithVehicle]
