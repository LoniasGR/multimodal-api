from sqlmodel import Field, Relationship, SQLModel

from .recommendation_request import RecommendationRequest


class SuggestionBase(SQLModel):
    request_id: int = Field(foreign_key="recommendationrequest.id")
    path: str
    selected: bool = Field(default=False)
    edges: int | None = None
    total_distance: float | None = None
    total_duration: float | None = None
    total_cost: float | None = None
    walk_count: int | None = None
    walk_distance: float | None = None
    car_count: int | None = None
    car_distance: float | None = None
    escooter_count: int | None = None
    escooter_distance: float | None = None
    sea_vessel_count: int | None = None
    sea_vessel_distance: float | None = None


class Suggestion(SuggestionBase, table=True):
    id: int | None = Field(primary_key=True)
    request: RecommendationRequest = Relationship()


class SuggestionPublic(SuggestionBase):
    request: RecommendationRequest | None = None
