from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomFieldBase(BaseModel):
    """Base schema for custom dynamic fields."""
    field_key: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Machine-readable snake_case identifier (e.g. friends_name, personal_mail)",
        examples=["friends_name"]
    )
    field_label: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Human-readable display label (e.g. Friend's Name, Personal Mail)",
        examples=["Friend's Name"]
    )
    field_value: str = Field(
        ...,
        min_length=1,
        description="Stored value of the custom attribute",
        examples=["Taha"]
    )
    category: Optional[str] = Field(
        "general",
        max_length=50,
        description="Optional category classification (e.g. contact, email, identity, general)",
        examples=["contact"]
    )


class CustomFieldCreate(CustomFieldBase):
    """Schema for creating a new custom field."""
    model_config = ConfigDict(extra="forbid")


class CustomFieldUpdate(BaseModel):
    """Schema for updating an existing custom field."""
    field_label: Optional[str] = Field(None, min_length=1, max_length=150)
    field_value: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, max_length=50)

    model_config = ConfigDict(extra="forbid")


class CustomFieldResponse(CustomFieldBase):
    """Schema for returning a custom field."""
    id: int = Field(..., description="Unique custom field identifier", examples=[1])
    user_id: int = Field(..., description="ID of the associated user", examples=[1])
    created_at: datetime = Field(..., description="Timestamp when record was created")
    updated_at: datetime = Field(..., description="Timestamp when record was last updated")

    model_config = ConfigDict(from_attributes=True)
