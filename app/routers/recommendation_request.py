from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import select

from ..dependencies import SessionDep, oauth2_scheme
from ..models import (
    RecommendationRequest,
    RecommendationRequestBase,
    RecommendationRequestPublic,
    Suggestion,
    SuggestionPublic,
    User,
)
from ..helpers import geojson_resp

router = APIRouter(
    prefix="/recommendation",
    tags=["recommendations"],
    dependencies=[Depends(oauth2_scheme)],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def request_recommendation(
    recommendation: RecommendationRequestBase, session: SessionDep
):
    db_rec_request = RecommendationRequest.model_validate(recommendation)

    db_user = session.exec(
        select(User).where(User.name == db_rec_request.user_id)
    ).first()

    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    session.add(db_rec_request)
    session.commit()
    session.refresh(db_rec_request)
    return geojson_resp


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
