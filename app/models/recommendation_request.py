from datetime import datetime

from pydantic import computed_field
from sqlmodel import Field, Relationship, SQLModel

from .location import Location
from .user import User


class RecommendationRequestBase(SQLModel):
    user_id: str = Field(foreign_key="user.name")
    origin_lat: float | None = Field(default=None, exclude=True)
    origin_lng: float | None = Field(default=None, exclude=True)
    destination_lat: float | None = Field(default=None, exclude=True)
    destination_lng: float | None = Field(default=None, exclude=True)
    mode: str
    walk: bool
    car: bool
    escooter: bool
    sea_vessel: bool

    @computed_field
    @property
    def include(self) -> dict:
        return {
            "walk": self.walk,
            "car": self.car,
            "escooter": self.escooter,
            "sea_vessel": self.sea_vessel,
        }

    @computed_field
    @property
    def origin(self) -> Location | None:
        if self.origin_lat is None or self.origin_lng is None:
            return None
        return Location(latitude=self.origin_lat, longitude=self.origin_lng)

    @origin.setter
    def origin(self, val: Location):
        self.origin_lat, self.origin_lng = val.latitude, val.longitude

    @computed_field
    @property
    def destination(self) -> Location | None:
        if self.destination_lat is None or self.destination_lng is None:
            return None
        return Location(latitude=self.destination_lat, longitude=self.destination_lng)

    @destination.setter
    def destination(self, val: Location):
        self.destination_lat, self.destination_lng = val.latitude, val.longitude


class RecommendationRequest(RecommendationRequestBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user: User = Relationship()
    date_requested: datetime = Field(default_factory=datetime.now)


class RecommendationRequestPublic(RecommendationRequestBase):
    user: User | None = None
