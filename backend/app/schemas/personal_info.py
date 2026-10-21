from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


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
    gender: Optional[str] = Field(
        None,
        max_length=30,
        description="Gender of the user (e.g. Male, Female, Other)",
        examples=["Male"]
    )
    date_of_birth: Optional[date] = Field(
        None,
        description="Date of birth in YYYY-MM-DD format",
        examples=["2002-05-15"]
    )
    profile_photo: Optional[str] = Field(
        None,
        description="Profile photograph (Data URI or URL)",
        examples=["data:image/png;base64,..."]
    )
    cnic_photo: Optional[str] = Field(
        None,
        description="CNIC / ID card document image (Data URI or URL)",
        examples=["data:image/png;base64,..."]
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
    graduation_year: Optional[str] = Field(
        None,
        max_length=50,
        description="Graduation year and/or GPA (e.g. 2026 | GPA: 3.8)",
        examples=["2026"]
    )
    major: Optional[str] = Field(
        None,
        max_length=150,
        description="Field of study or major",
        examples=["Computer Science"]
    )
    linkedin_url: Optional[str] = Field(
        None,
        max_length=500,
        description="LinkedIn profile URL",
        examples=["https://linkedin.com/in/muazamali"]
    )
    github_url: Optional[str] = Field(
        None,
        max_length=500,
        description="GitHub or portfolio URL",
        examples=["https://github.com/muazamali"]
    )
    bio: Optional[str] = Field(
        None,
        description="Professional bio or executive summary",
        examples=["Software Engineer with 3+ years experience in FastAPI and React."]
    )


class PersonalInfoCreate(PersonalInfoBase):
    """Schema for creating personal information. Requires full_name at minimum."""
    model_config = ConfigDict(extra="forbid")


class PersonalInfoUpdate(BaseModel):
    """Schema for updating personal information. All fields are optional."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    father_name: Optional[str] = Field(None, max_length=150)
    gender: Optional[str] = Field(None, max_length=30)
    date_of_birth: Optional[date] = None
    profile_photo: Optional[str] = None
    cnic_photo: Optional[str] = None
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
    graduation_year: Optional[str] = Field(None, max_length=50)
    major: Optional[str] = Field(None, max_length=150)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = Field(None)

    model_config = ConfigDict(extra="forbid")

    @field_validator("full_name")
    @classmethod
    def validate_full_name_not_null(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            raise ValueError("full_name cannot be null if provided")
        return v


class PersonalInfoResponse(PersonalInfoBase):
    """Schema for returning personal information."""
    id: int = Field(..., description="Unique personal info record ID", examples=[1])
    user_id: int = Field(..., description="ID of the user who owns this record", examples=[1])
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")

    model_config = ConfigDict(from_attributes=True)
