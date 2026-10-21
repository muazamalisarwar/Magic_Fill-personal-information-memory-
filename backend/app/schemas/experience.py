from datetime import date, datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator


class ExperienceBase(BaseModel):
    """Base fields for a work or internship experience."""
    company: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Company or organization name",
        examples=["Tech Innovations Inc."]
    )
    job_title: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Position or job title",
        examples=["Software Engineering Intern"]
    )
    start_date: date = Field(
        ...,
        description="Start date of the role (YYYY-MM-DD)",
        examples=["2025-06-01"]
    )
    end_date: Optional[date] = Field(
        None,
        description="End date of the role (YYYY-MM-DD). Null if currently active role.",
        examples=["2025-09-01"]
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Description of responsibilities and achievements",
        examples=["Built microservices using FastAPI and optimized database queries."]
    )
    skills: Optional[str] = Field(
        None,
        max_length=500,
        description="Comma-separated or listed skills used in this role",
        examples=["FastAPI, Python, PostgreSQL, Docker"]
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "ExperienceBase":
        """Verify that end_date is not earlier than start_date."""
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("end_date cannot be earlier than start_date")
        return self


class ExperienceCreate(ExperienceBase):
    """Schema for creating a new experience record."""
    model_config = ConfigDict(extra="forbid")


class ExperienceUpdate(BaseModel):
    """Schema for updating an existing experience record. All fields are optional."""
    company: Optional[str] = Field(None, min_length=1, max_length=200)
    job_title: Optional[str] = Field(None, min_length=1, max_length=150)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=2000)
    skills: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(extra="forbid")

    @field_validator("company", "job_title", "start_date")
    @classmethod
    def validate_non_nullable_fields(cls, v: Any) -> Any:
        if v is None:
            raise ValueError("Field cannot be null if provided")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "ExperienceUpdate":
        """Verify that end_date is not earlier than start_date if both are provided."""
        if self.start_date is not None and self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError("end_date cannot be earlier than start_date")
        return self


class ExperienceResponse(ExperienceBase):
    """Schema for returning experience record details."""
    id: int = Field(..., description="Unique experience record ID", examples=[1])
    user_id: int = Field(..., description="ID of the user who owns this record", examples=[1])
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")

    model_config = ConfigDict(from_attributes=True)
