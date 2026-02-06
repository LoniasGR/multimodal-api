import os

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import SQLModel, select

from app.auth.users import CurrentUser
from app.models.location import Location

from ..auth.users import oauth2_scheme
from ..db.db import SessionDep
from ..models import (
    RecommendationRequest,
    RecommendationRequestCreate,
    RecommendationRequestPublic,
    Suggestion,
    SuggestionPublic,
    User,
)

RECOMMENDATION_URL = os.getenv(
    "RECOMMENDATION_ENGINE_URL", "http://127.0.0.1:8001/suggest"
)
router = APIRouter(
    prefix="/recommendation",
    tags=["recommendations"],
    dependencies=[Depends(oauth2_scheme)],
)


class RecommendationEngineRequest(SQLModel):
    username: str
    avoid_cars: bool
    avoid_scooters: bool
    avoid_sea_vessels: bool
    origin: Location
    destination: Location
    minimizing_value: str

    def to_req(self):
        return {
            "username": self.username,
            "avoid_cars": self.avoid_cars,
            "avoid_scooters": self.avoid_scooters,
            "avoid_sea_vessels": self.avoid_sea_vessels,
            "origin": {
                "lat": self.origin.latitude,
                "lng": self.origin.longitude,
            },
            "destination": {
                "lat": self.destination.latitude,
                "lng": self.destination.longitude,
            },
            "minimizing_value": self.minimizing_value,
        }


@router.post("/", status_code=status.HTTP_201_CREATED)
def request_recommendation(
    recommendation: RecommendationRequestCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    db_rec_request = RecommendationRequest.model_validate(
        {
            **recommendation.model_dump(),
            "origin_lat": recommendation.origin.to_tuple()[0],
            "origin_lng": recommendation.origin.to_tuple()[1],
            "destination_lat": recommendation.destination.to_tuple()[0],
            "destination_lng": recommendation.destination.to_tuple()[1],
            "user_id": current_user.username,
        }
    )

    session.add(db_rec_request)
    session.commit()
    session.refresh(db_rec_request)
    req_body = RecommendationEngineRequest(
        username=current_user.username,
        avoid_cars=not recommendation.car,
        avoid_scooters=not recommendation.escooter,
        avoid_sea_vessels=not recommendation.sea_vessel,
        origin=recommendation.origin,
        destination=recommendation.destination,
        minimizing_value=recommendation.mode,
    )
    resp = requests.post(RECOMMENDATION_URL, json=req_body.to_req())
    if resp.status_code == 200:
        return resp.json()
    raise HTTPException(resp.status_code, resp.json())


@router.get("{request_id}", response_model=RecommendationRequestPublic)
def get_recommendation_request(request_id: int, session: SessionDep):
    db_request = session.exec(
        select(RecommendationRequest).where(RecommendationRequest.id == request_id)
    ).first()
    return db_request


@router.get("{request_id}/suggestions", response_model=list[SuggestionPublic])
def get_suggestions(request_id: int, session: SessionDep):
    db_suggestion = session.exec(
        select(Suggestion).where(Suggestion.request_id == request_id)
    ).all()
    return db_suggestion
