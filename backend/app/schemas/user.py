from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.personal_info import PersonalInfoResponse
from app.schemas.experience import ExperienceResponse
from app.schemas.custom_field import CustomFieldResponse
from app.schemas.document import DocumentResponse


class UserCreate(BaseModel):
    """
    Schema for creating a new User.
    Users can be created with an empty body or optional metadata.
    """
    model_config = ConfigDict(extra="forbid")


class UserResponse(BaseModel):
    """Schema for returning User details."""
    id: int = Field(..., description="Unique user identifier", examples=[1])
    created_at: datetime = Field(..., description="Timestamp when user was created")
    updated_at: datetime = Field(..., description="Timestamp when user was last updated")

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    """
    Unified schema representing a complete user memory profile,
    combining user identity, personal information, all experiences,
    extensible custom memory attributes, and saved documents/photos.
    """
    user: UserResponse
    personal_info: Optional[PersonalInfoResponse] = Field(
        None,
        description="User's personal, academic, and contact information if recorded"
    )
    experiences: List[ExperienceResponse] = Field(
        default_factory=list,
        description="Chronological list of all work experiences recorded for the user"
    )
    custom_fields: List[CustomFieldResponse] = Field(
        default_factory=list,
        description="Extensible custom attributes, contacts, and personal memory items"
    )
    documents: List[DocumentResponse] = Field(
        default_factory=list,
        description="Uploaded photos, identity documents (CNIC Front, CNIC Back, Passport), and credentials"
    )

    model_config = ConfigDict(from_attributes=True)


