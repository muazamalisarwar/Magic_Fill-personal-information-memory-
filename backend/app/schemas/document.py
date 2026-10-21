from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    """Base schema for document metadata."""
    doc_key: Optional[str] = Field(
        None,
        description="Machine identifier slug (e.g. cnic_front, cnic_back, profile_photo, passport)",
        max_length=100
    )
    title: Optional[str] = Field(
        None,
        description="Display title (e.g. CNIC Front, CNIC Back, Passport)",
        max_length=150
    )
    description: Optional[str] = Field(
        None,
        description="Natural language description of what the document or photograph represents (e.g. 'This is my CNIC front side')"
    )
    file_name: str = Field(
        ...,
        description="Original or inferred filename (e.g. cnic_front.jpg)",
        max_length=255
    )
    mime_type: str = Field(
        ...,
        description="MIME type (e.g. image/jpeg, image/png, application/pdf)",
        max_length=100
    )
    category: Optional[str] = Field(
        "identity",
        description="Category classification: identity, academic, profile, career, document",
        max_length=50
    )


class DocumentCreate(DocumentBase):
    """Schema for creating / uploading a document via JSON data URI."""
    user_id: int = Field(default=1, gt=0, description="User ID owning this document")
    file_data: str = Field(..., description="Base64 Data URI representing the file contents")
    file_size_bytes: Optional[int] = Field(None, ge=0, description="Size in bytes")

    model_config = ConfigDict(extra="ignore")


class DocumentUpdate(BaseModel):
    """Schema for updating document metadata."""
    title: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)

    model_config = ConfigDict(extra="forbid")


class DocumentResponse(BaseModel):
    """Schema for returning document records."""
    id: int = Field(..., description="Unique document ID")
    user_id: int = Field(..., description="Owner User ID")
    doc_key: str = Field(..., description="Identifier slug")
    title: str = Field(..., description="Display title")
    description: Optional[str] = Field(None, description="User description")
    file_name: str = Field(..., description="File name")
    mime_type: str = Field(..., description="MIME type")
    file_data: str = Field(..., description="Base64 Data URI")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    category: Optional[str] = Field("identity", description="Category")
    created_at: datetime = Field(..., description="Timestamp when created")
    updated_at: datetime = Field(..., description="Timestamp when last updated")

    model_config = ConfigDict(from_attributes=True)
