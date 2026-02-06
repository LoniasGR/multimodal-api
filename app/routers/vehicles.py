from fastapi import APIRouter, status, HTTPException
from sqlmodel import select

from app.auth.users import IsAdmin

from ..db.db import SessionDep
from ..models import (
    VehiclePublic,
    VehicleWithEvent,
    Vehicle,
    VehicleBase,
    VehicleEventBase,
    VehicleEvent,
    VehicleWithAllEvents,
)


router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/", response_model=list[VehiclePublic])
def read_vehicles(session: SessionDep):
    db_vehicles = session.exec(select(Vehicle)).all()
    return db_vehicles


@router.post("/", response_model=VehiclePublic, status_code=status.HTTP_201_CREATED)
def create_vehicle(vehicle: VehiclePublic, session: SessionDep):
    db_vehicle = Vehicle.model_validate(vehicle)
    db_vehicle.set_location(vehicle.location)
    session.add(db_vehicle)
    session.commit()
    session.refresh(db_vehicle)
    return db_vehicle


@router.get("/{vehicle_id}", response_model=VehicleWithEvent)
def read_vehicle(vehicle_id: int, session: SessionDep):
    db_vehicle = session.exec(select(Vehicle).where(Vehicle.id == vehicle_id)).first()
    if db_vehicle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "vehicle not found")

    return db_vehicle


@router.delete("/{vehicle_id}", status_code=status.HTTP_200_OK)
def delete_vehicle(vehicle_id: int, session: SessionDep, is_admin: IsAdmin):
    if not is_admin:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Only admins can delete vehicles"
        )

    db_vehicle = session.exec(select(Vehicle).where(Vehicle.id == vehicle_id)).first()
    if db_vehicle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "vehicle not found")
    session.delete(db_vehicle)
    session.commit()
    return


@router.get("/{vehicle_id}/history", response_model=VehicleWithAllEvents)
def read_vehicle_history(vehicle_id: int, session: SessionDep):
    db_vehicle = session.exec(select(Vehicle).where(Vehicle.id == vehicle_id)).one()

    return db_vehicle


@router.put("/{vehicle_id}", response_model=VehiclePublic | None)
def update_vehicle(vehicle_id: int, vehicle: VehicleBase, session: SessionDep):
    db_vehicle = session.get(Vehicle, vehicle_id)
    if db_vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found"
        )

    vehicle_data = vehicle.model_dump(exclude_unset=True)
    db_vehicle.sqlmodel_update(vehicle_data)

    session.add(db_vehicle)
    session.commit()
    session.refresh(db_vehicle)

    return db_vehicle


@router.post(
    "/{vehicle_id}/history",
    response_model=VehicleEventBase,
    status_code=status.HTTP_201_CREATED,
)
def update_history(vehicle_id: int, event: VehicleEventBase, session: SessionDep):
    db_vehicle = session.get(Vehicle, vehicle_id)
    if db_vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found"
        )
    event_dict = event.model_dump()
    event_dict["vehicle_id"] = vehicle_id
    db_event = VehicleEvent.model_validate(event_dict)
    session.add(db_event)
    session.commit()

    db_vehicle.latitude = db_event.latitude
    db_vehicle.longitude = db_event.longitude
    db_vehicle.latest_event_id = db_event.id
    session.add(db_vehicle)
    session.commit()
    session.refresh(db_event)
    return db_event
