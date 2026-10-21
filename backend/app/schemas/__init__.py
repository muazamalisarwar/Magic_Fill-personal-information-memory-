"""Schemas package exporting Pydantic request and response models."""
from app.schemas.common import APIResponse, ErrorResponse, HealthResponse
from app.schemas.user import UserCreate, UserResponse, UserProfileResponse
from app.schemas.personal_info import (
    PersonalInfoBase,
    PersonalInfoCreate,
    PersonalInfoUpdate,
    PersonalInfoResponse,
)
from app.schemas.experience import (
    ExperienceBase,
    ExperienceCreate,
    ExperienceUpdate,
    ExperienceResponse,
)
from app.schemas.matching import (
    DetectedField,
    FieldMatchRequest,
    FieldMapping,
    FieldMatchResponse,
)

__all__ = [
    "APIResponse",
    "ErrorResponse",
    "HealthResponse",
    "UserCreate",
    "UserResponse",
    "UserProfileResponse",
    "PersonalInfoBase",
    "PersonalInfoCreate",
    "PersonalInfoUpdate",
    "PersonalInfoResponse",
    "ExperienceBase",
    "ExperienceCreate",
    "ExperienceUpdate",
    "ExperienceResponse",
    "DetectedField",
    "FieldMatchRequest",
    "FieldMapping",
    "FieldMatchResponse",
]
