from datetime import datetime

from fastapi import APIRouter, status
from sqlmodel import select

from ..db.db import SessionDep
from ..models import EnvironmentalConditions

router = APIRouter(
    prefix="/environmental-conditions",
    tags=["environmental conditions"],
)


@router.get("/", response_model=list[EnvironmentalConditions])
def read_environmental_conditions(
    session: SessionDep,
    time: datetime | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
):
    query = select(EnvironmentalConditions)
    if time or latitude or longitude:
        if time:
            query = query.where(EnvironmentalConditions.time == time)
        if latitude:
            query = query.where(EnvironmentalConditions.latitude == latitude)
        if longitude:
            query = query.where(EnvironmentalConditions.longitude == longitude)
    db_environmental_conditions = session.exec(query).all()
    return db_environmental_conditions


@router.post(
    "/", response_model=EnvironmentalConditions, status_code=status.HTTP_201_CREATED
)
def create_environmental_conditions(
    environmental_conditions: EnvironmentalConditions, session: SessionDep
):
    db_environmental_conditions = EnvironmentalConditions.model_validate(
        environmental_conditions
    )
    session.add(db_environmental_conditions)
    session.commit()
    session.refresh(db_environmental_conditions)

    return db_environmental_conditions
