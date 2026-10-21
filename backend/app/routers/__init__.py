"""Routers package exporting APIRouter instances."""
from app.routers.users import router as users_router
from app.routers.personal_info import router as personal_info_router
from app.routers.experiences import router as experiences_router
from app.routers.matching import router as matching_router
from app.routers.memory import router as memory_router
from app.routers.custom_fields import router as custom_fields_router
from app.routers.documents import router as documents_router
from app.routers.auth import router as auth_router

__all__ = [
    "users_router",
    "personal_info_router",
    "experiences_router",
    "matching_router",
    "memory_router",
    "custom_fields_router",
    "documents_router",
    "auth_router",
]



