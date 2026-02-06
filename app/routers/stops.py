from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from ..db.db import SessionDep
from ..models import StopCreate, Stop, Location, StopPublic

router = APIRouter(prefix="/stops", tags=["stops"])


@router.get("/", response_model=list[StopPublic])
def read_stops(session: SessionDep):
    stops = session.exec(select(Stop)).all()
    ret_stops = []
    for db_stop in stops:
        if (db_stop.latitude is None) or (db_stop.longitude is None):
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, "stop with empty location found"
            )
        ret_stop = StopPublic.model_validate(
            {
                **db_stop.model_dump(),
                "location": Location(
                    latitude=db_stop.latitude, longitude=db_stop.longitude
                ),
            }
        )
        ret_stops.append(ret_stop)
    return ret_stops


@router.post("/", response_model=StopPublic, status_code=status.HTTP_201_CREATED)
def create_stop(stop: StopCreate, session: SessionDep):
    if stop.location is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Stop location must be provided"
        )
    db_stop = Stop.model_validate(
        {
            **stop.model_dump(),
            "latitude": stop.location.latitude,
            "longitude": stop.location.longitude,
        }
    )

    exists = session.exec(select(Stop).where(Stop.name == stop.name)).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stop with name '{stop.name}' already exists",
        )
    session.add(db_stop)
    session.commit()
    session.refresh(db_stop)

    if (db_stop.latitude is None) or (db_stop.longitude is None):
        raise ValueError("latitude and longitude cannot be None")

    ret_stop = StopPublic.model_validate(
        {
            **db_stop.model_dump(),
            "location": Location(
                latitude=db_stop.latitude, longitude=db_stop.longitude
            ),
        }
    )

    return ret_stop
