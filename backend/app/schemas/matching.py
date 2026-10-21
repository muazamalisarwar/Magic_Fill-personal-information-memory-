from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DetectedField(BaseModel):
    """Schema representing a single form input element detected in a web page DOM."""
    field_id: str = Field(..., description="Unique client-side identifier or DOM selector for the field")
    name: Optional[str] = Field(None, description="HTML name attribute")
    label: Optional[str] = Field(None, description="Extracted label or preceding text")
    placeholder: Optional[str] = Field(None, description="HTML placeholder attribute")
    aria_label: Optional[str] = Field(None, description="HTML aria-label or accessible name attribute")
    input_type: Optional[str] = Field("text", description="HTML input type (text, email, tel, number, select, textarea, radio, checkbox, date, range, file, button, etc.)")
    options: Optional[List[str]] = Field(None, description="Available options if the input is a select dropdown or radio group")
    tag_name: Optional[str] = Field(None, description="HTML tag name (input, select, textarea, button)")
    value: Optional[str] = Field(None, description="Current value or option value of the element")
    checked: Optional[bool] = Field(None, description="Checked state for radio or checkbox")
    min: Optional[str] = Field(None, description="Min attribute for date, number, range")
    max: Optional[str] = Field(None, description="Max attribute for date, number, range")
    step: Optional[str] = Field(None, description="Step attribute for number, range")
    accept: Optional[str] = Field(None, description="Accept attribute for file upload")
    role: Optional[str] = Field(None, description="ARIA role (switch, radio, checkbox, etc.)")

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def reconcile_type(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "type" in data and ("input_type" not in data or not data["input_type"]):
                data["input_type"] = data["type"]
        return data


class FieldMatchRequest(BaseModel):
    """Request payload sent by browser extension to map detected website form fields to personal memory."""
    user_id: Optional[int] = Field(None, gt=0, description="ID of the user whose memory records should be matched", examples=[1])
    fields: List[DetectedField] = Field(..., min_length=1, description="List of detected form fields on the active webpage")
    form_context: Optional[str] = Field(None, description="Optional page context, e.g. 'Job Application', 'University Admission'")

    model_config = ConfigDict(extra="ignore")


class FieldMapping(BaseModel):
    """Result of mapping a detected field to a stored personal memory attribute."""
    field_id: str = Field(..., description="ID of the detected form field")
    memory_key: str = Field(..., description="Key path in user memory (e.g. 'personal_info.full_name', 'experiences[0].company')")
    value: str = Field(..., description="Canonical value retrieved from user memory to autofill")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the match (0.0 to 1.0)")
    reason: str = Field(..., description="Brief explanation of why this mapping was selected")
    source: str = Field("deterministic", description="Resolution strategy used ('deterministic' or 'llm')")

    model_config = ConfigDict(from_attributes=True)


class FieldMatchResponse(BaseModel):
    """Response containing matched fields ready for browser autofill and any unresolved fields."""
    mappings: List[FieldMapping] = Field(default_factory=list, description="List of successfully mapped fields")
    unresolved_fields: List[str] = Field(default_factory=list, description="IDs of fields that could not be confidently mapped")
    total_detected: int = Field(..., description="Total number of fields submitted in the request")
    total_mapped: int = Field(..., description="Number of fields successfully mapped")

    model_config = ConfigDict(from_attributes=True)
