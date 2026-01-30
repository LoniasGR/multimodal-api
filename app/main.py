from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from . import models, routers
from .dependencies import SessionDep, create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routers.users_router)
app.include_router(routers.vehicles_router)
app.include_router(routers.stops_router)
app.include_router(routers.environmental_conditions_router)
app.include_router(routers.traffic_router)
app.include_router(routers.recommendation_request_router)
app.include_router(routers.auth_router)


@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")


@app.get("/trip/{id}", response_model=models.TripPublicWithVehicles)
def get_trip(id: int, session: SessionDep):
    return session.get(models.Trip, id)


@app.post("/test")
def test(session: SessionDep):
    from datetime import datetime

    from .models import Trip

    trip = Trip(
        start_time=datetime.now(), end_time=datetime.now(), recommendation_request_id=1
    )
    vehicle = session.get(models.Vehicle, 1)
    if vehicle is None:
        return None

    tripVehicle = models.TripVehicle(
        trip=trip, vehicle=vehicle, duration=10.0, distance=10.0
    )
    session.add(trip)
    session.add(tripVehicle)

    session.commit()
    # session.refresh(trip)
