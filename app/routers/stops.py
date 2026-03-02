from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlmodel import select

from ..db.db import SessionDep
from ..auth.users import admin_dependency
from ..models import StopCreate, Stop, Location, StopPublic
from ..geojson.geojson import generate_poi_geojson

router = APIRouter(prefix="/stops", tags=["stops"])


@router.get("/", response_model=list[StopPublic])
def read_stops(
    session: SessionDep,
    geojson: bool = Query(False, description="Return GeoJSON FeatureCollection"),
):
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
    if geojson:
        return JSONResponse(
            content=generate_poi_geojson(ret_stops),
            media_type="application/geo+json",
        )
    return ret_stops


@router.post(
    "/",
    response_model=StopPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[admin_dependency],
)
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


@router.delete(
    "/{stop_id}", status_code=status.HTTP_200_OK, dependencies=[admin_dependency]
)
def delete_stop(stop_id: int, session: SessionDep):
    db_stop = session.exec(select(Stop).where(Stop.id == stop_id)).first()
    if db_stop is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "stop not found")
    session.delete(db_stop)
    session.commit()
    return
