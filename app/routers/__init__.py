from .users import router as users_router
from .vehicles import router as vehicles_router
from .stops import router as stops_router
from .environmental_conditions import router as environmental_conditions_router
from .traffic import router as traffic_router
from .recommendation_request import router as recommendation_request_router
from .auth import router as auth_router

__all__ = [
    "users_router",
    "vehicles_router",
    "stops_router",
    "environmental_conditions_router",
    "traffic_router",
    "recommendation_request_router",
    "auth_router",
]
