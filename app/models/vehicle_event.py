from datetime import datetime
from typing import Any

from pydantic import computed_field, model_validator
from sqlmodel import Field, Relationship, SQLModel

from .location import Location
from .vehicle import Vehicle


class VehicleEventBase(SQLModel):
    timestamp: datetime
    user_id: str | None = Field(foreign_key="user.name", default=None)
    event_type: str
    action_performed: str | None = None
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)

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


class VehicleEvent(VehicleEventBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    vehicle_id: int = Field(foreign_key="vehicle.id")
    vehicle: Vehicle = Relationship(
        back_populates="all_history",
        sa_relationship_kwargs={"foreign_keys": "[VehicleEvent.vehicle_id]"},
    )
