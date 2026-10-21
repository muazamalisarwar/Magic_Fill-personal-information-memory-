from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class FieldCategory(str, Enum):
    PERSONAL_INFO = "PERSONAL_INFO"
    PROFESSIONAL_INFO = "PROFESSIONAL_INFO"
    COMMUNICATION_CONTENT = "COMMUNICATION_CONTENT"
    TRANSACTIONAL = "TRANSACTIONAL"
    SENSITIVE_OR_SECRET = "SENSITIVE_OR_SECRET"
    UNKNOWN = "UNKNOWN"


class LearningActionType(str, Enum):
    NEW_ATTRIBUTE = "NEW_ATTRIBUTE"
    UPDATE_ATTRIBUTE = "UPDATE_ATTRIBUTE"
    NO_ACTION = "NO_ACTION"


class EvaluateFieldRequest(BaseModel):
    field_name: Optional[str] = Field(None, description="DOM element name or id attribute")
    label: Optional[str] = Field(None, description="Associated visible label text or placeholder")
    value: str = Field(..., min_length=1, description="Value entered into the field by user")
    input_type: Optional[str] = Field("text", description="HTML input type or tag (text, textarea, etc.)")
    placeholder: Optional[str] = Field(None, description="Placeholder attribute if present")
    form_context: Optional[str] = Field(None, description="Contextual form heading or parent form title")
    page_title: Optional[str] = Field(None, description="Title of the active webpage")

    model_config = ConfigDict(extra="ignore")


class EvaluateFieldResponse(BaseModel):
    category: FieldCategory
    is_learnable: bool
    action_type: LearningActionType
    canonical_key: Optional[str] = None
    field_label: Optional[str] = None
    existing_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class CommitLearningRequest(BaseModel):
    action_type: LearningActionType = Field(..., description="Action to perform: NEW_ATTRIBUTE or UPDATE_ATTRIBUTE")
    canonical_key: str = Field(..., min_length=1, description="Normalized snake_case key (e.g. linkedin_url, phone)")
    field_label: str = Field(..., min_length=1, description="Human-readable label for the attribute")
    value: str = Field(..., min_length=1, description="Value to save or update in memory")
    category: Optional[str] = Field("general", description="Category for custom field (e.g. social, contact, professional)")

    model_config = ConfigDict(extra="ignore")


from app.schemas.user import UserProfileResponse


class CommitLearningResponse(BaseModel):
    saved: bool
    message: str
    canonical_key: str
    action_taken: str
    updated_profile: Optional[UserProfileResponse] = None

    model_config = ConfigDict(extra="ignore")
