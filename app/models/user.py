from enum import Enum
from typing import Any

from pydantic import computed_field, model_validator
from sqlmodel import Field, SQLModel

from .location import Location


class Sex(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class AgeGroup(str, Enum):
    CHILD = "CHILD"
    TEEN = "TEEN"
    ADULT = "ADULT"
    SENIOR = "SENIOR"


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserBase(SQLModel):
    username: str
    name: str
    age_group: AgeGroup = Field(default=None)
    sex: Sex | None = Field(default=None)
    role: UserRole = Field(default=UserRole.USER)
    latitude: float | None = Field(default=None, exclude=True)
    longitude: float | None = Field(default=None, exclude=True)
    is_available: bool = Field(default=True)

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


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    password_hash: str
