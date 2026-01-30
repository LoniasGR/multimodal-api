from fastapi import APIRouter, status
from sqlmodel import select

from ..dependencies import SessionDep
from ..models import Stop, StopDB, Location

router = APIRouter(prefix="/stops", tags=["stops"])


@router.get("/", response_model=list[Stop])
def read_stops(session: SessionDep):
    stops = session.exec(select(StopDB)).all()
    ret_stops = []
    for db_stop in stops:
        ret_stop = Stop.model_validate(db_stop)
        if (db_stop.lat is None) or (db_stop.lng is None):
            raise ValueError("lat and lng cannot be None")
        ret_stop.loc = Location(latitude=db_stop.lat, longitude=db_stop.lng)
        ret_stops.append(ret_stop)
    return stops


@router.post("/", response_model=Stop, status_code=status.HTTP_201_CREATED)
def create_stop(stop: Stop, session: SessionDep):
    db_stop = StopDB.model_validate(stop)
    if stop.loc is None:
        raise ValueError("Stop location must be provided")
    db_stop.lat = stop.loc.latitude
    db_stop.lng = stop.loc.longitude
    session.add(db_stop)
    session.commit()
    session.refresh(db_stop)

    ret_stop = Stop.model_validate(db_stop)
    if (db_stop.lat is None) or (db_stop.lng is None):
        raise ValueError("lat and lng cannot be None")
    ret_stop.loc = Location(latitude=db_stop.lat, longitude=db_stop.lng)

    return ret_stop
