from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PersonalInfoBase(BaseModel):
    """Base fields for Personal Information."""
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Full legal name of the user",
        examples=["Muazam Ali"]
    )
    father_name: Optional[str] = Field(
        None,
        max_length=150,
        description="Father's name",
        examples=["Muhammad Ali"]
    )
    date_of_birth: Optional[date] = Field(
        None,
        description="Date of birth in YYYY-MM-DD format",
        examples=["2002-05-15"]
    )
    cnic: Optional[str] = Field(
        None,
        max_length=20,
        description="National Identity Card number",
        examples=["35202-1234567-1"]
    )
    phone: Optional[str] = Field(
        None,
        min_length=7,
        max_length=30,
        description="Contact phone number",
        examples=["+92 300 1234567"]
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Primary email address",
        examples=["muazam.ali@example.com"]
    )
    address: Optional[str] = Field(
        None,
        max_length=500,
        description="Residential street address",
        examples=["House 123, Street 4, Sector G-10"]
    )
    city: Optional[str] = Field(
        None,
        max_length=100,
        description="City of residence",
        examples=["Islamabad"]
    )
    postal_code: Optional[str] = Field(
        None,
        max_length=20,
        description="Postal/ZIP code",
        examples=["44000"]
    )
    country: Optional[str] = Field(
        None,
        max_length=100,
        description="Country of residence",
        examples=["Pakistan"]
    )
    university: Optional[str] = Field(
        None,
        max_length=200,
        description="Name of current or graduated university",
        examples=["FAST NUCES"]
    )
    degree: Optional[str] = Field(
        None,
        max_length=150,
        description="Degree program",
        examples=["BS Computer Science"]
    )
    department: Optional[str] = Field(
        None,
        max_length=150,
        description="Academic department",
        examples=["Department of Computer Science"]
    )
    semester: Optional[str] = Field(
        None,
        max_length=50,
        description="Current semester or academic standing",
        examples=["8th Semester"]
    )
    registration_number: Optional[str] = Field(
        None,
        max_length=100,
        description="University student roll number or registration ID",
        examples=["21F-1234"]
    )


class PersonalInfoCreate(PersonalInfoBase):
    """Schema for creating personal information. Requires full_name at minimum."""
    model_config = ConfigDict(extra="forbid")


class PersonalInfoUpdate(BaseModel):
    """Schema for updating personal information. All fields are optional."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    father_name: Optional[str] = Field(None, max_length=150)
    date_of_birth: Optional[date] = None
    cnic: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, min_length=7, max_length=30)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    university: Optional[str] = Field(None, max_length=200)
    degree: Optional[str] = Field(None, max_length=150)
    department: Optional[str] = Field(None, max_length=150)
    semester: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=100)

    model_config = ConfigDict(extra="forbid")


class PersonalInfoResponse(PersonalInfoBase):
    """Schema for returning personal information."""
    id: int = Field(..., description="Unique personal info record ID", examples=[1])
    user_id: int = Field(..., description="ID of the user who owns this record", examples=[1])
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")

    model_config = ConfigDict(from_attributes=True)
