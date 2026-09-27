from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


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
