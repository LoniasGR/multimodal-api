from annotated_types import T
from fastapi import APIRouter, status
from sqlmodel import select
from datetime import datetime
from ..dependencies import SessionDep
from ..models import Traffic


router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.get("/", response_model=list[Traffic])
def read_traffic(
    session: SessionDep,
    time: datetime | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
):
    query = select(Traffic)
    if time or latitude or longitude:
        if time:
            query = query.where(Traffic.time == time)
        if latitude:
            query = query.where(Traffic.latitude == latitude)
        if longitude:
            query = query.where(Traffic.longitude == longitude)
    db_traffic = session.exec(query).all()
    return db_traffic


@router.post("/", response_model=Traffic, status_code=status.HTTP_201_CREATED)
def create_traffic(traffic: Traffic, session: SessionDep):
    db_traffic = Traffic.model_validate(traffic)
    session.add(db_traffic)
    session.commit()
    session.refresh(db_traffic)

    return db_traffic
