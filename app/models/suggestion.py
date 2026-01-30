from sqlmodel import Field, Relationship, SQLModel

from .recommendation_request import RecommendationRequest


class SuggestionBase(SQLModel):
    request_id: int = Field(foreign_key="recommendationrequest.id")
    path: str
    selected: bool
    edges: int
    total_distance: float
    total_duration: float
    total_cost: float
    walk_count: int
    walk_distance: float
    car_count: int
    car_distance: float
    escooter_count: int
    escooter_distance: float
    sea_vessel_count: int
    sea_vessel_distanc: float


class Suggestion(SuggestionBase, table=True):
    id: int | None = Field(primary_key=True)
    request: RecommendationRequest = Relationship()


class SuggestionPublic(SuggestionBase):
    request: RecommendationRequest | None = None
