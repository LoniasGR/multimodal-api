import os

import geojson
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.auth.users import CurrentUser

from ..auth.users import oauth2_scheme
from ..db.db import SessionDep
from ..models import (
    RecommendationRequest,
    RecommendationRequestCreate,
    RecommendationRequestPublic,
    RecommendationEngineRequest,
    Suggestion,
    SuggestionPublic,
)

RECOMMENDATION_URL = os.getenv(
    "RECOMMENDATION_ENGINE_URL", "http://127.0.0.1:8001/suggest"
)
router = APIRouter(
    prefix="/recommendation",
    tags=["recommendations"],
    dependencies=[Depends(oauth2_scheme)],
)


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
            "walk": recommendation.transport_preferences.walk,
            "car": recommendation.transport_preferences.car,
            "escooter": recommendation.transport_preferences.escooter,
            "sea_vessel": recommendation.transport_preferences.sea_vessel,
        }
    )

    session.add(db_rec_request)
    session.commit()
    session.refresh(db_rec_request)
    req_body = RecommendationEngineRequest(
        username=current_user.username,
        avoid_cars=not recommendation.transport_preferences.car,
        avoid_scooters=not recommendation.transport_preferences.escooter,
        avoid_sea_vessels=not recommendation.transport_preferences.sea_vessel,
        origin=recommendation.origin,
        destination=recommendation.destination,
        minimizing_value=recommendation.mode,
    )
    resp = requests.post(RECOMMENDATION_URL, json=req_body.to_req())
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.json())

    data = resp.json()
    for trip in data["trips"]:
        suggestion_db = Suggestion.model_validate(
            {
                "id": None,
                "request_id": db_rec_request.id,
                "path": geojson.dumps(trip["geojson"]),
                **trip["properties"],
            }
        )
        session.add(suggestion_db)
        session.commit()
        session.refresh(suggestion_db)
        trip["properties"]["id"] = suggestion_db.id
    return data


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
