from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.common import APIResponse
from app.schemas.user import UserProfileResponse, UserResponse
from app.schemas.personal_info import PersonalInfoResponse
from app.schemas.experience import ExperienceResponse
from app.schemas.custom_field import CustomFieldResponse
from app.schemas.document import DocumentResponse
from app.services.extraction_service import (
    extract_structured_memory_from_text,
    extract_text_from_file_bytes,
    save_extracted_memory_to_database,
)
from app.services.user_service import get_user_profile, create_user
from app.services.personal_info_service import delete_personal_info
from app.schemas.learning import (
    EvaluateFieldRequest,
    EvaluateFieldResponse,
    CommitLearningRequest,
    CommitLearningResponse,
)
from app.services.learning_service import (
    evaluate_field_for_learning,
    commit_learned_field,
)
from app.database.models import User, Experience, CustomField, UserDocument

router = APIRouter(
    prefix="/memory",
    tags=["Personal Memory Management"]
)


class RawTextIngestRequest(BaseModel):
    raw_text: str = Field(..., min_length=3, description="Unstructured biography, CV text, or notes")
    user_id: int = Field(default=1, gt=0, description="User ID to save memory against")
    auto_save: bool = Field(default=True, description="Whether to automatically commit extracted records to database")
    model_config = ConfigDict(extra="forbid")


class ExtractionResponse(BaseModel):
    extracted: Dict[str, Any]
    profile: Optional[UserProfileResponse] = None
    saved: bool
    raw_text: Optional[str] = None


def _build_profile_response(profile_data: Dict[str, Any]) -> UserProfileResponse:
    """Helper to convert user profile dictionary to UserProfileResponse schema."""
    return UserProfileResponse(
        user=UserResponse.model_validate(profile_data["user"]),
        personal_info=PersonalInfoResponse.model_validate(profile_data["personal_info"]) if profile_data.get("personal_info") else None,
        experiences=[ExperienceResponse.model_validate(exp) for exp in profile_data.get("experiences", [])],
        custom_fields=[CustomFieldResponse.model_validate(cf) for cf in profile_data.get("custom_fields", [])],
        documents=[DocumentResponse.model_validate(doc) for doc in profile_data.get("documents", [])],
    )


from app.services import auth_service

@router.post(
    "/extract-raw",
    response_model=APIResponse[ExtractionResponse],
    status_code=status.HTTP_200_OK,
    summary="Extract structured profile from raw natural text and optionally save",
    description="Processes free-form text or pasted resumes using Groq LLM, converts it to structured JSON, and saves to the database."
)
@router.post(
    "/extract-text",
    response_model=APIResponse[ExtractionResponse],
    status_code=status.HTTP_200_OK,
    summary="Extract structured profile from raw text (alias)",
    include_in_schema=False
)
@router.put(
    "/extract-raw",
    response_model=APIResponse[ExtractionResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
@router.put(
    "/extract-text",
    response_model=APIResponse[ExtractionResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
async def extract_raw_text_endpoint(
    payload: RawTextIngestRequest,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[ExtractionResponse]:
    """Extracts structured personal memory from unstructured raw text using Groq LLM."""
    target_user_id = current_user.id if current_user else payload.user_id
    extracted = await extract_structured_memory_from_text(raw_text=payload.raw_text)

    saved_profile = None
    if payload.auto_save:
        profile_data = save_extracted_memory_to_database(
            db=db,
            user_id=target_user_id,
            extracted_data=extracted
        )
        saved_profile = _build_profile_response(profile_data)

    return APIResponse(
        success=True,
        message="Successfully processed and extracted personal memory with Groq AI" if payload.auto_save else "Extracted candidate memory preview",
        data=ExtractionResponse(
            extracted=extracted,
            profile=saved_profile,
            saved=payload.auto_save
        )
    )


@router.post(
    "/parse-text",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Parse raw text from uploaded document (PDF/TXT/MD)",
    description="Extracts raw plain text from an uploaded document for immediate frontend preview and character/word counting."
)
async def parse_document_text_endpoint(
    file: UploadFile = File(...),
) -> APIResponse[Dict[str, Any]]:
    """Extracts raw text from a document without running LLM extraction yet."""
    content_bytes = await file.read()
    raw_text = extract_text_from_file_bytes(content_bytes=content_bytes, filename=file.filename or "doc.txt")
    char_count = len(raw_text)
    word_count = len(raw_text.split()) if raw_text else 0

    if not raw_text or not raw_text.strip():
        return APIResponse(
            success=False,
            message="No readable text found in document. If this is a scanned PDF or image, please copy/paste the text directly.",
            data={"raw_text": "", "char_count": 0, "word_count": 0, "filename": file.filename}
        )

    return APIResponse(
        success=True,
        message=f"Scanned {char_count} characters ({word_count} words) from {file.filename}",
        data={
            "raw_text": raw_text,
            "char_count": char_count,
            "word_count": word_count,
            "filename": file.filename
        }
    )


@router.post(
    "/upload-document",
    response_model=APIResponse[ExtractionResponse],
    status_code=status.HTTP_200_OK,
    summary="Upload CV/Resume document (PDF or Text) for AI extraction",
    description="Accepts a PDF or text file, extracts its contents, runs Groq LLM extraction, and saves to the user's personal memory."
)
async def upload_document_endpoint(
    file: UploadFile = File(...),
    user_id: int = Form(default=1),
    auto_save: bool = Form(default=True),
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[ExtractionResponse]:
    """Uploads and parses a document (PDF / text) to populate personal memory."""
    target_user_id = current_user.id if current_user else user_id
    content_bytes = await file.read()
    raw_text = extract_text_from_file_bytes(content_bytes=content_bytes, filename=file.filename or "doc.txt")
    
    extracted = await extract_structured_memory_from_text(raw_text=raw_text)

    saved_profile = None
    if auto_save:
        profile_data = save_extracted_memory_to_database(
            db=db,
            user_id=target_user_id,
            extracted_data=extracted
        )
        saved_profile = _build_profile_response(profile_data)

    return APIResponse(
        success=True,
        message=f"Successfully extracted personal memory from {file.filename}",
        data=ExtractionResponse(
            extracted=extracted,
            profile=saved_profile,
            saved=auto_save,
            raw_text=raw_text
        )
    )


@router.get(
    "/current",
    response_model=APIResponse[UserProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current active user personal memory",
    description="Fetches the current user profile or auto-initializes User #1 if empty."
)
def get_current_memory_endpoint(
    user_id: int = 1,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[UserProfileResponse]:
    """Retrieves the active personal memory profile for the authenticated user."""
    target_user_id = current_user.id if current_user else user_id

    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        user = User(id=target_user_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    profile_data = get_user_profile(db=db, user_id=target_user_id)
    return APIResponse(
        success=True,
        message="Active personal memory retrieved",
        data=_build_profile_response(profile_data)
    )


@router.delete(
    "/clear",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Clear personal memory for user",
    description="Cleans out personal info, experiences, and custom fields for test resetting."
)
def clear_memory_endpoint(
    user_id: int = 1,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[None]:
    """Resets personal memory records for the active user."""
    target_user_id = current_user.id if current_user else user_id

    user = db.query(User).filter(User.id == target_user_id).first()
    if user:
        if user.personal_info:
            db.delete(user.personal_info)
        db.query(Experience).filter(Experience.user_id == target_user_id).delete()
        db.query(CustomField).filter(CustomField.user_id == target_user_id).delete()
        db.query(UserDocument).filter(UserDocument.user_id == target_user_id).delete()
        db.commit()

    return APIResponse(
        success=True,
        message="Personal memory cleared successfully",
        data=None
    )


@router.post(
    "/evaluate-field",
    response_model=APIResponse[EvaluateFieldResponse],
    status_code=status.HTTP_200_OK,
    summary="Evaluate input field for intelligent personal memory learning",
    description="Classifies a field into PERSONAL_INFO, PROFESSIONAL_INFO, or excluded categories, compares against user memory, and determines if a save/update prompt should be shown."
)
async def evaluate_field_endpoint(
    payload: EvaluateFieldRequest,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[EvaluateFieldResponse]:
    """Evaluates whether a field completed on a website represents learnable personal/professional memory."""
    target_user_id = current_user.id if current_user else 1
    result = await evaluate_field_for_learning(
        db=db,
        user_id=target_user_id,
        request=payload
    )
    return APIResponse(
        success=True,
        message="Field evaluation completed",
        data=result
    )


@router.post(
    "/commit-learning",
    response_model=APIResponse[CommitLearningResponse],
    status_code=status.HTTP_200_OK,
    summary="Commit user-approved field learning to database",
    description="Saves or updates a newly learned personal or professional attribute to the authenticated user's records."
)
def commit_learning_endpoint(
    payload: CommitLearningRequest,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[CommitLearningResponse]:
    """Commits an approved attribute to personal memory."""
    target_user_id = current_user.id if current_user else 1
    raw_res = commit_learned_field(
        db=db,
        user_id=target_user_id,
        request=payload
    )
    profile_dto = _build_profile_response(raw_res["profile_data"]) if raw_res.get("profile_data") else None
    return APIResponse(
        success=raw_res["saved"],
        message=raw_res["message"],
        data=CommitLearningResponse(
            saved=raw_res["saved"],
            message=raw_res["message"],
            canonical_key=raw_res["canonical_key"],
            action_taken=raw_res["action_taken"],
            updated_profile=profile_dto
        )
    )


class UniversalMemoryUpdateRequest(BaseModel):
    type: Optional[str] = None
    id: Optional[int] = None
    key: Optional[str] = None
    label: Optional[str] = None
    field_key: Optional[str] = None
    field_label: Optional[str] = None
    value: Optional[str] = None
    field_value: Optional[str] = None
    category: Optional[str] = "general"
    model_config = ConfigDict(extra="allow")


@router.put(
    "/update",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Universal Memory Update Endpoint",
    description="Updates personal profile, custom attributes, or experiences dynamically."
)
@router.post(
    "/update",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
@router.patch(
    "/update",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def update_memory_generic_endpoint(
    payload: UniversalMemoryUpdateRequest,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[Dict[str, Any]]:
    """Universal memory update endpoint accepting type, key, and value via PUT, POST, or PATCH."""
    target_user_id = current_user.id if current_user else 1
    new_val = payload.value if payload.value is not None else payload.field_value
    target_key = payload.key or payload.field_key or "custom_note"
    record_type = payload.type or "custom_field"

    from app.services import personal_info_service, custom_field_service
    from app.schemas.personal_info import PersonalInfoUpdate, PersonalInfoCreate
    from app.schemas.custom_field import CustomFieldCreate, CustomFieldUpdate

    if record_type == "personal_info" or target_key in ("full_name", "phone", "address", "city", "country", "postal_code", "linkedin_url", "github_url", "bio", "university", "degree", "major", "graduation_year"):
        info = personal_info_service.get_personal_info_by_user_id(db=db, user_id=target_user_id)
        update_dict = {target_key: new_val}
        if not info:
            info = personal_info_service.create_personal_info(
                db=db,
                user_id=target_user_id,
                info_in=PersonalInfoCreate(**update_dict)
            )
        else:
            info = personal_info_service.update_personal_info(
                db=db,
                user_id=target_user_id,
                info_in=PersonalInfoUpdate(**update_dict)
            )
        return APIResponse(
            success=True,
            message="Personal record updated successfully",
            data={"type": "personal_info", "key": target_key, "value": new_val}
        )

    # Custom Field update / create
    if payload.id:
        try:
            cf = custom_field_service.update_custom_field(
                db=db,
                field_id=payload.id,
                field_in=CustomFieldUpdate(field_value=str(new_val))
            )
            return APIResponse(
                success=True,
                message="Custom attribute updated successfully",
                data={"type": "custom_field", "id": cf.id, "value": cf.field_value}
            )
        except Exception:
            pass

    # Create new custom field if doesn't exist
    cf = custom_field_service.create_custom_field(
        db=db,
        user_id=target_user_id,
        field_in=CustomFieldCreate(
            field_key=target_key,
            field_label=payload.label or payload.field_label or target_key.replace("_", " ").title(),
            field_value=str(new_val or ""),
            category=payload.category or "general"
        )
    )
    return APIResponse(
        success=True,
        message="Memory attribute saved successfully",
        data={"type": "custom_field", "id": cf.id, "key": cf.field_key, "value": cf.field_value}
    )


@router.post(
    "/reset",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Reset and wipe all personal memory for the user",
    description="Resets all personal info, work experiences, custom fields, and uploaded user documents/assets for the current user."
)
@router.delete(
    "/reset",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def reset_memory_endpoint(
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[Dict[str, Any]]:
    """Wipes all personal memory records (personal info, experiences, custom fields, documents) for the authenticated user."""
    target_user_id = current_user.id if current_user else 1

    # 1. Delete all experiences
    deleted_exp = db.query(Experience).filter(Experience.user_id == target_user_id).delete()

    # 2. Delete all custom fields
    deleted_cf = db.query(CustomField).filter(CustomField.user_id == target_user_id).delete()

    # 3. Delete all uploaded documents / media assets
    deleted_docs = db.query(UserDocument).filter(UserDocument.user_id == target_user_id).delete()

    # 4. Reset personal info entity
    from app.database.models import PersonalInfo
    info = db.query(PersonalInfo).filter(PersonalInfo.user_id == target_user_id).first()
    if info:
        db.delete(info)

    db.commit()

    return APIResponse(
        success=True,
        message="Personal memory vault has been completely reset to a clean slate.",
        data={
            "user_id": target_user_id,
            "status": "cleared",
            "deleted_experiences": deleted_exp,
            "deleted_custom_fields": deleted_cf,
            "deleted_documents": deleted_docs
        }
    )



