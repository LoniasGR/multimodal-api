from random import randint

from fastapi import Depends
from sqlmodel import Field, Session, SQLModel, create_engine
from typing_extensions import Annotated

from .data_structures import (
    AgeGroupValue,
    Location,
    SexValue,
    Stop,
    StopType,
    TransportType,
    User,
    Vehicle,
)

SQLITE_FILE_NAME = "database.db"


class UserDB(SQLModel, table=True):
    __tablename__ = "user"
    username: str = Field(primary_key=True)
    name: str
    age_group: str
    sex: str = Field(default=None)
    role: str
    latitude: float
    longitude: float
    is_available: bool = Field(default=True)

    def to_user(self) -> User:
        return User(
            id=randint(0, 100),
            age_group=AgeGroupValue[self.age_group],
            sex=SexValue[self.sex],
            loc=Location(lat=self.latitude, lng=self.longitude),
        )


class VehicleDB(SQLModel, table=True):
    __tablename__ = "vehicle"

    id: int = Field(primary_key=True)
    type: str
    latitude: float
    longitude: float
    status: str

    def to_vehicle(self) -> Vehicle:
        return Vehicle(
            id=self.id,
            type=TransportType[self.type],
            loc=Location(lat=self.latitude, lng=self.longitude),
            is_available=(self.status == "IDLE"),
        )


class StopDB(SQLModel, table=True):
    __tablename__ = "stop"

    name: str = Field(unique=True, index=True)
    type: str
    id: int = Field(primary_key=True)
    latitude: float
    longitude: float

    def to_stop(self) -> Stop:
        return Stop(
            id=self.id,
            name=self.name,
            type=StopType[self.type],
            loc=Location(lat=self.latitude, lng=self.longitude),
        )


sqlite_url = f"sqlite:///{SQLITE_FILE_NAME}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
