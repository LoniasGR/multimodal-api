from enum import StrEnum
from typing import TYPE_CHECKING, Any, Optional

from pydantic import computed_field, model_validator
from sqlmodel import Field, Relationship, SQLModel

from .location import Location
from .transport_type import TransportType

if TYPE_CHECKING:
    from .trip_vehicle import TripVehicle
    from .vehicle_event import VehicleEvent


class VehicleStatus(StrEnum):
    CREATING = "CREATING"
    IN_USE = "IN_USE"
    RESERVED = "RESERVED"
    IDLE = "IDLE"
    CHARGING = "CHARGING"
    UNAVAILABLE = "UNAVAILABLE"


class Vehicle(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: VehicleStatus = Field(default=VehicleStatus.IDLE)
    latitude: float | None = Field(default=None, exclude=True)
    longitude: float | None = Field(default=None, exclude=True)
    type: TransportType
    trips: list["TripVehicle"] = Relationship(back_populates="vehicle")
    # Foreign key to the latest history entry
    latest_event_id: int | None = Field(default=None, foreign_key="vehicleevent.id")
    # Relationship to latest history
    latest_event: Optional["VehicleEvent"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Vehicle.latest_event_id]",
        }
    )
    # Relationship to all history entries
    all_history: list["VehicleEvent"] = Relationship(
        back_populates="vehicle",
        sa_relationship_kwargs={"foreign_keys": "[VehicleEvent.vehicle_id]"},
    )

    def set_location(self, location: Location) -> None:
        self.latitude = location.latitude
        self.longitude = location.longitude

    # For reading - returns location object in API responses
    @computed_field
    @property
    def location(self) -> Location | None:
        if self.latitude is None or self.longitude is None:
            return None
        return Location(latitude=self.latitude, longitude=self.longitude)

    # For writing - accepts location object in API requests
    @model_validator(mode="before")
    @classmethod
    def extract_location(cls, data: Any) -> Any:
        if isinstance(data, dict) and "location" in data:
            loc = data.pop("location")
            data["latitude"] = loc["latitude"]
            data["longitude"] = loc["longitude"]
        return data


class VehicleBase(SQLModel):
    status: VehicleStatus = Field(default=VehicleStatus.IDLE)
    location: Location


class VehiclePublic(VehicleBase):
    id: int | None = Field(default=None, primary_key=True)
    type: TransportType


class VehicleWithEvent(VehiclePublic):
    latest_event: Optional["VehicleEvent"] = None


class VehicleWithAllEvents(VehiclePublic):
    all_history: list["VehicleEvent"] = []
