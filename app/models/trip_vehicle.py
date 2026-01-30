from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .trip import Trip
    from .vehicle import Vehicle, VehicleCreate


class TripVehicleBase(SQLModel):
    duration: float
    distance: float


class TripVehicle(TripVehicleBase, table=True):
    vehicle_id: int | None = Field(
        default=None, foreign_key="vehicle.id", primary_key=True
    )
    trip_id: int | None = Field(default=None, foreign_key="trip.id", primary_key=True)

    vehicle: "Vehicle" = Relationship(back_populates="trips")
    trip: "Trip" = Relationship(back_populates="vehicles")


class TripVehiclePublicWithVehicle(TripVehicleBase):
    if TYPE_CHECKING:
        vehicle: "VehicleCreate"
