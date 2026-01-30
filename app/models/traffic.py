from datetime import datetime
from typing import Any

from pydantic import computed_field, model_validator
from sqlmodel import Field, SQLModel

from .location import Location


class Traffic(SQLModel, table=True):
    latitude: float = Field(primary_key=True, exclude=True)
    longitude: float = Field(primary_key=True, exclude=True)
    time: datetime = Field(primary_key=True)

    # For reading - returns location object in API responses
    @computed_field
    @property
    def location(self) -> Location:
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
