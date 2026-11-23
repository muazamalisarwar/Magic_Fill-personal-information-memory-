import datetime
import json
import logging
import re
from typing import Any, Dict, List, Optional
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
from app.services.custom_field_service import upsert_custom_field_by_key
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
from app.database.models import User, Experience, CustomField, UserDocument, PersonalInfo
from app.ai.prompts import COPILOT_CHAT_SYSTEM_PROMPT
from app.ai.provider_manager import AIProviderManager

logger = logging.getLogger("app.routers.memory")

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
    extracted = await extract_structured_memory_from_text(raw_text=payload.raw_text, user_id=target_user_id, db=db)

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
        message="Successfully processed and extracted personal memory" if payload.auto_save else "Extracted candidate memory preview",
        data=ExtractionResponse(
            extracted=extracted,
            profile=saved_profile,
            saved=payload.auto_save
        )
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
    
    extracted = await extract_structured_memory_from_text(raw_text=raw_text, user_id=target_user_id, db=db)

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
            saved=auto_save
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


# -----------------------------------------------------------------------------
# 9. AI Memory Copilot Conversational Chat & Real-Time Mutation
# -----------------------------------------------------------------------------

class CopilotChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class CopilotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt or update instruction")
    history: Optional[List[CopilotChatMessage]] = Field(default_factory=list)
    user_id: Optional[int] = Field(default=1)


class CopilotFieldUpdate(BaseModel):
    field_type: str = Field(default="personal_info", description="personal_info | custom_field | experience")
    key: str
    label: str
    old_value: Optional[str] = None
    new_value: str
    action: str = Field(default="UPDATE", description="UPDATE | ADD")


class CopilotChatResult(BaseModel):
    reply: str
    intent: str = Field(default="QUERY", description="QUERY | UPDATE")
    updates: List[CopilotFieldUpdate] = Field(default_factory=list)
    updated_profile: Optional[UserProfileResponse] = None


COPILOT_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "for", "with", "at", "by", "from",
    "to", "in", "on", "into", "onto", "over", "under", "above", "below", "of", "off",
    "what", "whats", "which", "who", "whom", "whose", "why", "when", "where", "how",
    "you", "your", "yours", "yourself", "me", "my", "mine", "myself", "i", "we", "us",
    "our", "ours", "he", "him", "his", "she", "her", "hers", "it", "its", "they", "them",
    "their", "theirs", "this", "that", "these", "those",
    "is", "are", "was", "were", "be", "been", "being", "am",
    "do", "does", "did", "done", "doing",
    "have", "has", "had", "having",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    "own", "any", "all", "some", "such", "no", "not", "only", "same", "so", "than",
    "too", "very", "just", "now", "then", "there", "here",
    "get", "got", "give", "given", "make", "made", "know", "known", "tell", "show",
    "saved", "save", "saving", "stored", "store", "memory", "vault", "record",
    "please", "thanks", "thank", "okay", "ok", "yes", "yeah", "sure", "well", "hello", "hi"
}


def _copilot_local_grounded_fallback(
    message: str,
    user_profile: Dict[str, Any],
    user: User,
    p_info: Optional[PersonalInfo],
    db: Session,
    target_user_id: int,
    history: Optional[List[CopilotChatMessage]] = None
) -> Dict[str, Any]:
    """Smart grounded fallback when external LLM is offline or in testing."""
    msg_lower = message.lower().strip()
    p_data = user_profile.get("personal_info") or {}
    exps = user_profile.get("experiences") or []
    cfs = user_profile.get("custom_fields") or []

    # 0. STRICT DOMAIN RESTRICTION: Reject off-topic non-memory requests
    off_topic_patterns = [
        r"\b(?:write|compose|generate|draft)\s+(?:a\s+)?(?:poem|poetry|song|lyrics|story|novel|essay|speech|script|joke|haiku|riddle)\b",
        r"\b(?:how\s+to\s+code|how\s+do\s+i\s+code|implement|algorithm|binary\s+search|leetcode|write\s+a\s+function|write\s+python|write\s+javascript|write\s+html)\b",
        r"\b(?:what\s+is\s+the\s+capital|who\s+is\s+the\s+president|who\s+is\s+the\s+prime\s+minister|who\s+won|weather\s+in|recipe\s+for|translate\s+to|tell\s+me\s+a\s+joke)\b",
        r"\b(?:solve|calculate|what\s+is\s+\d+\s*[\+\-\*\/])\b",
    ]
    if any(re.search(pat, msg_lower) for pat in off_topic_patterns):
        return {
            "intent": "QUERY",
            "reply": "I am your dedicated Magic Fill AI Memory Copilot. I can only assist with showing, querying, or updating your personal memory vault (such as your contact info, education, career experience, or custom saved attributes). Let me know what detail you'd like to check or update!",
            "updates": []
        }

    # Typo normalization for robust natural language understanding
    msg_normalized = msg_lower
    typo_map = {
        "favroite": "favorite",
        "favourite": "favorite",
        "favorit": "favorite",
        "sabed": "saved",
        "seved": "saved",
        "chnage": "change",
        "chagne": "change",
        "updat": "update",
        "adress": "address",
        "adrees": "address",
        "addrss": "address",
        "emial": "email",
        "phne": "phone",
        "fone": "phone",
        "universty": "university",
        "degre": "degree",
        "exprnc": "experience",
        "experiance": "experience",
    }
    for typo, clean in typo_map.items():
        msg_normalized = re.sub(rf"\b{typo}\b", clean, msg_normalized)

    # 0.1 Conversational Courtesies & Acknowledgments (e.g. 'ok thank you', 'thanks', 'thank you so much', 'awesome', 'great', 'got it')
    thanks_pattern = r"^(?:(?:ok|okay|alright|sure|yes|yeah|so|well)\s*[,:\-]?\s*)?(?:thank\s+you|thanks|thx|thank\s*u|thankyou|much\s+appreciated|appreciate\s+it)(?:\s+(?:so\s+much|a\s+lot|very\s+much|copilot|buddy|mate))?[\.!\s]*$"
    acknowledgment_pattern = r"^(?:(?:ok|okay|alright|sure|yes|yeah)\s*[,:\-]?\s*)?(?:great|awesome|perfect|excellent|wonderful|sounds\s+good|got\s+it|understood|cool|done|no\s+problem)[\.!\s]*$"
    farewell_pattern = r"^(?:bye|goodbye|see\s+you|see\s+ya|have\s+a\s+good\s+(?:day|night))[\.!\s]*$"

    if re.search(thanks_pattern, msg_normalized) or re.search(acknowledgment_pattern, msg_normalized):
        return {
            "intent": "QUERY",
            "reply": "You're very welcome! Let me know whenever you'd like to check or update anything in your memory vault.",
            "updates": []
        }

    if re.search(farewell_pattern, msg_normalized):
        return {
            "intent": "QUERY",
            "reply": "Goodbye! Your personal memory vault is safely stored and ready whenever you need it.",
            "updates": []
        }

    # 0.2 Friendly Greetings
    greeting_pattern = r"^(?:hi|hello|hey|salam|assalam(?:\s+o\s+alaikum)?|greetings|good\s+(?:morning|afternoon|evening|day))(?:\s+(?:there|copilot|magic\s+fill))?[\.!\s]*$"
    if re.search(greeting_pattern, msg_normalized):
        full_name = p_data.get("full_name") or user.full_name or "there"
        return {
            "intent": "QUERY",
            "reply": f"Hello {full_name}! I am your AI Memory Copilot. You can ask me to show any detail in your memory vault (e.g. *'What is currently saved my name?'*, *'What address you know about me?'*), or command me to update your memory (e.g. *'Update my phone to 0326-8848703'* or *'My favorite fruit is mango'*).",
            "updates": []
        }

    # 1. Update Detection Patterns (typo-tolerant: update, change, chnage, chagne, set, make, modify, save, store, record)
    # Name
    name_m = re.search(r"(?:update|change|chnage|chagne|set|make|modify|save|store|record)\s+(?:my\s+)?(?:current\s+)?(?:name|full\s*name|legal\s*name)\s+(?:to\s+|is\s+|as\s+|to\s+this\s+|:\s*)?['\"]?([^'\"\.,\n]+)['\"]?", msg_normalized)
    if name_m and not any(w in msg_normalized for w in ["father", "mother", "guardian", "friend", "grandfather", "company", "boss"]):
        raw_val = message[name_m.start(1):name_m.end(1)].strip(" :'\"")
        new_name = raw_val.title()
        old_name = p_data.get("full_name") or user.full_name or "Muazam Ali"
        user.full_name = new_name
        if p_info:
            p_info.full_name = new_name
        db.commit()
        return {
            "intent": "UPDATE",
            "reply": f"I have updated your legal full name in your memory vault from **{old_name}** to **{new_name}**.",
            "updates": [{
                "field_type": "personal_info",
                "key": "full_name",
                "label": "Legal Full Name",
                "old_value": old_name,
                "new_value": new_name,
                "action": "UPDATE"
            }]
        }

    # Address
    addr_m = re.search(r"(?:update|change|chnage|chagne|set|make|modify|save|store|record)\s+(?:my\s+)?(?:current\s+)?(?:residential\s+)?(?:address|location|residence|addr)\s+(?:to\s+|is\s+|as\s+|to\s+this\s+|:\s*)?['\"]?([^'\"\n]+)['\"]?", msg_normalized)
    if addr_m:
        new_addr = message[addr_m.start(1):addr_m.end(1)].strip(" :'\"")
        old_addr = p_data.get("address") or "Not set"
        if p_info:
            p_info.address = new_addr
        db.commit()
        return {
            "intent": "UPDATE",
            "reply": f"I have updated your address in your memory vault to **{new_addr}**.",
            "updates": [{
                "field_type": "personal_info",
                "key": "address",
                "label": "Address",
                "old_value": old_addr,
                "new_value": new_addr,
                "action": "UPDATE"
            }]
        }

    # Contextual Multi-Turn Updates (e.g. user asks "what is my address?" then says "update to Narang Mandi...", "update to this Narang Mandi...", "change it to X", "make it X", "OK CHNAGE IT TO TAHA ALI")
    context_val = None
    CONV_PREFIX = r"(?:(?:ok|okay|alright|sure|yes|yeah|so|now|then|well|please|can\s+you|could\s+you)\s*[,:\-]?\s*)*"
    context_patterns = [
        rf"^{CONV_PREFIX}(?:update|change|set|make|modify)\s+(?:it\s+|this\s+|that\s+)?to(?:\s+this)?\s*[:\-]?\s*['\"]?([^'\"\n]+)['\"]?",
        rf"^{CONV_PREFIX}(?:update|change|set|make|modify)\s+(?:it|this|that)\s+(?:as|with|to)\s+['\"]?([^'\"\n]+)['\"]?",
        rf"^{CONV_PREFIX}(?:replace|swap)\s+(?:it|this|that)\s+(?:with|by)\s+['\"]?([^'\"\n]+)['\"]?",
        rf"^{CONV_PREFIX}(?:no[,\s]+)?(?:actually\s+)?(?:change\s+to|update\s+to|make\s+it|set\s+to)\s+['\"]?([^'\"\n]+)['\"]?",
        rf"^{CONV_PREFIX}(?:it\s+is|its|it\'s)\s+['\"]?([^'\"\n]+)['\"]?\s+(?:now|instead)",
        rf"^{CONV_PREFIX}(?:update|change|set)\s*[:\-]\s*['\"]?([^'\"\n]+)['\"]?",
        r"\b(?:update|change|set|make|modify)\s+(?:it|this|that)\s+(?:to|as|with)\s+['\"]?([^'\"\n]+)['\"]?",
        r"\b(?:update|change|set)\s+(?:it\s+|this\s+|that\s+)?to\s+['\"]?([^'\"\n]+)['\"]?",
    ]
    for cp in context_patterns:
        cm = re.search(cp, msg_normalized)
        if cm:
            context_val = message[cm.start(1):cm.end(1)].strip(" :'\"")
            break

    if context_val:
        prior_user_text = ""
        prior_asst_text = ""
        prior_all_text = ""
        if history:
            for h in reversed(history):
                role = getattr(h, "role", None) or (h.get("role") if isinstance(h, dict) else "")
                content = (getattr(h, "content", None) or (h.get("content") if isinstance(h, dict) else "") or "").lower()
                if content and content != msg_lower:
                    prior_all_text += " " + content
                    if role == "user" and not prior_user_text:
                        prior_user_text = content
                    elif role == "assistant" and not prior_asst_text:
                        prior_asst_text = content

        def _has_kw(target_words: List[str]) -> bool:
            return (
                any(w in prior_user_text for w in target_words)
                or any(w in prior_asst_text for w in target_words)
                or any(w in prior_all_text for w in target_words)
            )

        def _in_recent(target_words: List[str]) -> bool:
            return any(w in prior_user_text for w in target_words) or any(w in prior_asst_text for w in target_words)

        is_addr_heuristic = any(loc_kw in context_val.lower() for loc_kw in ["street", "st.", "road", "rd.", "lahore", "karachi", "islamabad", "pakistan", "avenue", "lane", "house", "flat", "city", "block", "phase", "district", "village", "zafar"])
        is_phone_heuristic = bool(re.match(r"^[\d\+\-\s]{8,}$", context_val))
        is_email_heuristic = "@" in context_val and "." in context_val

        # 0. Father / Guardian Context
        is_father_recent = _in_recent(["father", "guardian", "father's name", "father name", "guardian name"])
        if is_father_recent and not is_addr_heuristic and not is_phone_heuristic and not is_email_heuristic:
            old_father = p_data.get("father_name") or "Not set"
            if p_info:
                p_info.father_name = context_val.title()
            db.commit()
            return {
                "intent": "UPDATE",
                "reply": f"I have updated your Father / Guardian name in your memory vault to **{context_val.title()}**.",
                "updates": [{
                    "field_type": "personal_info",
                    "key": "father_name",
                    "label": "Father's Name",
                    "old_value": old_father,
                    "new_value": context_val.title(),
                    "action": "UPDATE"
                }]
            }

        # 1. Name Context (prioritize when most recent turn asked about or displayed legal name, full name, or user asked who am i)
        is_name_recent = _in_recent(["name", "who am i", "call me", "named", "legal name", "saved name", "full name"]) and not is_father_recent and not _in_recent(["mother", "friend", "grandfather", "company", "boss"])
        if is_name_recent and not is_addr_heuristic and not is_phone_heuristic and not is_email_heuristic:
            old_name = p_data.get("full_name") or user.full_name or "Muazam Ali"
            user.full_name = context_val.title()
            if p_info:
                p_info.full_name = context_val.title()
            db.commit()
            return {
                "intent": "UPDATE",
                "reply": f"I have updated your legal full name in your memory vault to **{context_val.title()}**.",
                "updates": [{
                    "field_type": "personal_info",
                    "key": "full_name",
                    "label": "Legal Full Name",
                    "old_value": old_name,
                    "new_value": context_val.title(),
                    "action": "UPDATE"
                }]
            }

        # 2. Address Context
        if _in_recent(["address", "street", "road", "residence", "where do i live", "live", "location"]) or is_addr_heuristic:
            old_addr = p_data.get("address") or "Not set"
            if p_info:
                p_info.address = context_val
            db.commit()
            return {
                "intent": "UPDATE",
                "reply": f"I have updated your address in your memory vault to **{context_val}**.",
                "updates": [{
                    "field_type": "personal_info",
                    "key": "address",
                    "label": "Address",
                    "old_value": old_addr,
                    "new_value": context_val,
                    "action": "UPDATE"
                }]
            }

        # 3. Phone Context
        if _in_recent(["phone", "mobile", "cell", "contact number", "call"]) or is_phone_heuristic:
            old_phone = p_data.get("phone") or "Not set"
            if p_info:
                p_info.phone = context_val
            db.commit()
            return {
                "intent": "UPDATE",
                "reply": f"I have updated your phone number in your memory vault to **{context_val}**.",
                "updates": [{
                    "field_type": "personal_info",
                    "key": "phone",
                    "label": "Primary Phone",
                    "old_value": old_phone,
                    "new_value": context_val,
                    "action": "UPDATE"
                }]
            }

        # 4. Name Context via broader history
        if _has_kw(["name", "who am i", "call me"]) and not is_addr_heuristic and not is_phone_heuristic and not is_email_heuristic:
            old_name = p_data.get("full_name") or user.full_name or "Muazam Ali"
            user.full_name = context_val.title()
            if p_info:
                p_info.full_name = context_val.title()
            db.commit()
            return {
                "intent": "UPDATE",
                "reply": f"I have updated your legal full name in your memory vault to **{context_val.title()}**.",
                "updates": [{
                    "field_type": "personal_info",
                    "key": "full_name",
                    "label": "Legal Full Name",
                    "old_value": old_name,
                    "new_value": context_val.title(),
                    "action": "UPDATE"
                }]
            }

        # Email Context
        elif _has_kw(["email", "mail"]) or ("@" in context_val and "." in context_val):
            old_email = p_data.get("email") or "Not set"
            if p_info:
                p_info.email = context_val
            db.commit()
            return {
                "intent": "UPDATE",
                "reply": f"I have updated your contact email in your memory vault to **{context_val}**.",
                "updates": [{
                    "field_type": "personal_info",
                    "key": "email",
                    "label": "Contact Email",
                    "old_value": old_email,
                    "new_value": context_val,
                    "action": "UPDATE"
                }]
            }

        # University / Degree Context
        elif any(w in prior_user_text for w in ["degree", "qualification", "major"]) or any(w in context_val.lower().split() for w in ["bs", "ms", "bachelor", "master", "phd", "degree"]):
            old_deg = p_data.get("degree") or "Not set"
            if p_info:
                p_info.degree = context_val
            db.commit()
            return {
                "intent": "UPDATE",
                "reply": f"I have updated your degree in your memory vault to **{context_val}**.",
                "updates": [{
                    "field_type": "personal_info",
                    "key": "degree",
                    "label": "Degree",
                    "old_value": old_deg,
                    "new_value": context_val,
                    "action": "UPDATE"
                }]
            }
        elif _has_kw(["university", "college", "institution"]):
            old_univ = p_data.get("university") or "Not set"
            if p_info:
                p_info.university = context_val
            db.commit()
            return {
                "intent": "UPDATE",
                "reply": f"I have updated your university in your memory vault to **{context_val}**.",
                "updates": [{
                    "field_type": "personal_info",
                    "key": "university",
                    "label": "University",
                    "old_value": old_univ,
                    "new_value": context_val,
                    "action": "UPDATE"
                }]
            }
        elif _has_kw(["degree", "qualification", "major", "educat"]):
            old_deg = p_data.get("degree") or "Not set"
            if p_info:
                p_info.degree = context_val
            db.commit()
            return {
                "intent": "UPDATE",
                "reply": f"I have updated your degree in your memory vault to **{context_val}**.",
                "updates": [{
                    "field_type": "personal_info",
                    "key": "degree",
                    "label": "Degree",
                    "old_value": old_deg,
                    "new_value": context_val,
                    "action": "UPDATE"
                }]
            }

        # Custom fields context
        for cf in cfs:
            k = (cf.get("field_key") or "").lower()
            lbl = (cf.get("field_label") or "").lower()
            combined_text = re.sub(r"[^a-z0-9\s]+", " ", f"{k.replace('_', ' ')} {lbl}")
            substantive_kws = [w for w in combined_text.split() if len(w) >= 3 and w not in COPILOT_STOP_WORDS]
            if substantive_kws and any(re.search(rf"\b{re.escape(w)}\b", prior_all_text) for w in substantive_kws):
                upsert_custom_field_by_key(
                    db=db,
                    user_id=target_user_id,
                    field_key=cf.get("field_key"),
                    field_label=cf.get("field_label"),
                    field_value=context_val,
                    category=cf.get("category") or "personal"
                )
                db.commit()
                return {
                    "intent": "UPDATE",
                    "reply": f"I have updated your **{cf.get('field_label') or cf.get('field_key')}** in your memory vault to **{context_val}**.",
                    "updates": [{
                        "field_type": "custom_field",
                        "key": cf.get("field_key"),
                        "label": cf.get("field_label") or cf.get("field_key"),
                        "old_value": cf.get("field_value"),
                        "new_value": context_val,
                        "action": "UPDATE"
                    }]
                }

        # Value heuristic inference if prior keywords weren't explicit
        if "@" in context_val and "." in context_val:
            old_email = p_data.get("email") or "Not set"
            if p_info:
                p_info.email = context_val
            db.commit()
            return {
                "intent": "UPDATE",
                "reply": f"I have updated your contact email in your memory vault to **{context_val}**.",
                "updates": [{
                    "field_type": "personal_info",
                    "key": "email",
                    "label": "Contact Email",
                    "old_value": old_email,
                    "new_value": context_val,
                    "action": "UPDATE"
                }]
            }
        elif re.match(r"^[\d\+\-\s]{8,}$", context_val):
            old_phone = p_data.get("phone") or "Not set"
            if p_info:
                p_info.phone = context_val
            db.commit()
            return {
                "intent": "UPDATE",
                "reply": f"I have updated your phone number in your memory vault to **{context_val}**.",
                "updates": [{
                    "field_type": "personal_info",
                    "key": "phone",
                    "label": "Primary Phone",
                    "old_value": old_phone,
                    "new_value": context_val,
                    "action": "UPDATE"
                }]
            }

    # Phone
    phone_m = re.search(r"(?:update|change|chnage|chagne|set|make|modify|save|store|record)\s+(?:my\s+)?(?:phone(?:\s*number)?|mobile(?:\s*number)?|cell(?:\s*number)?|contact\s*number)\s+(?:to\s+|is\s+|as\s+|to\s+this\s+|:\s*)?['\"]?([0-9\+\-\s]+)['\"]?", msg_normalized)
    if phone_m:
        new_phone = message[phone_m.start(1):phone_m.end(1)].strip(" :'\"")
        old_phone = p_data.get("phone") or "Not set"
        if p_info:
            p_info.phone = new_phone
        db.commit()
        return {
            "intent": "UPDATE",
            "reply": f"I have updated your phone number in your memory vault to **{new_phone}**.",
            "updates": [{
                "field_type": "personal_info",
                "key": "phone",
                "label": "Primary Phone",
                "old_value": old_phone,
                "new_value": new_phone,
                "action": "UPDATE"
            }]
        }

    # Email
    email_m = re.search(r"(?:update|change|chnage|chagne|set|make|modify|save|store|record)\s+(?:my\s+)?(?:email(?:\s*address)?|mail)\s+(?:to\s+|is\s+|as\s+|to\s+this\s+|:\s*)?['\"]?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)['\"]?", msg_normalized)
    if email_m:
        new_email = message[email_m.start(1):email_m.end(1)].strip(" :'\"")
        old_email = p_data.get("email") or "Not set"
        if p_info:
            p_info.email = new_email
        db.commit()
        return {
            "intent": "UPDATE",
            "reply": f"I have updated your contact email in your memory vault to **{new_email}**.",
            "updates": [{
                "field_type": "personal_info",
                "key": "email",
                "label": "Contact Email",
                "old_value": old_email,
                "new_value": new_email,
                "action": "UPDATE"
            }]
        }

    # Father / Guardian Name
    father_m = re.search(
        r"(?:update|change|chnage|chagne|set|make|modify|save|store|record|add)\s+(?:my\s+)?(?:father(?:'s)?(?:\s*name)?|guardian(?:\s*name)?)\s+(?:to\s+|is\s+|as\s+|to\s+this\s+|:\s*)?['\"]?([^'\"\.,\n]+)['\"]?",
        msg_normalized
    )
    if not father_m:
        father_m = re.search(
            r"^(?:(?:remember\s+(?:that\s+)?)|save\s+)?(?:my\s+)?(?:father(?:'s)?(?:\s*name)?|guardian(?:\s*name)?)\s+(?:is|=|to|as)\s+['\"]?([^'\"\.,\n]+)['\"]?",
            msg_normalized
        )
    if father_m:
        new_father = message[father_m.start(1):father_m.end(1)].strip(" :'\"").title()
        old_father = p_data.get("father_name") or "Not set"
        if p_info:
            p_info.father_name = new_father
        db.commit()
        return {
            "intent": "UPDATE",
            "reply": f"I have updated your Father / Guardian name in your memory vault to **{new_father}**.",
            "updates": [{
                "field_type": "personal_info",
                "key": "father_name",
                "label": "Father's Name",
                "old_value": old_father,
                "new_value": new_father,
                "action": "UPDATE"
            }]
        }

    # Add Skill
    skill_m = re.search(r"(?:add|insert|set|append)\s+(?:a\s+)?(?:new\s+)?skill\s*(?::|\s+to\s+|\s+is\s+|\s+)?['\"]?([^'\"\n]+)['\"]?", msg_lower)
    if skill_m:
        new_skill = message[skill_m.start(1):skill_m.end(1)].strip(" :'\"")
        upsert_custom_field_by_key(
            db=db,
            user_id=target_user_id,
            field_key="technical_skills",
            field_label="Technical Skills",
            field_value=new_skill,
            category="professional"
        )
        db.commit()
        return {
            "intent": "UPDATE",
            "reply": f"I have added **{new_skill}** to your skills in your memory vault.",
            "updates": [{
                "field_type": "custom_field",
                "key": "technical_skills",
                "label": "Technical Skills",
                "old_value": None,
                "new_value": new_skill,
                "action": "ADD"
            }]
        }

    # Natural attribute statement (e.g. 'my favorite fruit is mango', 'my expected salary is $150k')
    stmt_m = re.search(r"^(?:my|remember\s+(?:that\s+)?my)\s+([a-zA-Z0-9\s_'-]+?)\s+(?:is|to|are|=)\s+['\"]?([^'\"\n]+)['\"]?", msg_normalized)
    if stmt_m:
        raw_key_phrase = stmt_m.group(1).strip()
        val_phrase = message[stmt_m.start(2):stmt_m.end(2)].strip(" :'\"")
        if val_phrase and raw_key_phrase not in ("name", "full name", "phone", "email", "address", "father", "father name"):
            snake_key = re.sub(r"[^a-z0-9_]+", "_", raw_key_phrase).strip("_")
            clean_label = raw_key_phrase.replace("_", " ").title()

            # If attribute belongs to personal_info, update personal_info
            if p_info and hasattr(p_info, snake_key):
                old_val = getattr(p_info, snake_key)
                setattr(p_info, snake_key, val_phrase)
                db.commit()
                return {
                    "intent": "UPDATE",
                    "reply": f"I have updated your **{clean_label}** in your memory vault to **{val_phrase}**.",
                    "updates": [{
                        "field_type": "personal_info",
                        "key": snake_key,
                        "label": clean_label,
                        "old_value": str(old_val) if old_val else None,
                        "new_value": val_phrase,
                        "action": "UPDATE"
                    }]
                }
            else:
                upsert_custom_field_by_key(
                    db=db,
                    user_id=target_user_id,
                    field_key=snake_key,
                    field_label=clean_label,
                    field_value=val_phrase,
                    category="personal"
                )
                db.commit()
                return {
                    "intent": "UPDATE",
                    "reply": f"I have saved your **{clean_label}** as **{val_phrase}** in your memory vault.",
                    "updates": [{
                        "field_type": "custom_field",
                        "key": snake_key,
                        "label": clean_label,
                        "old_value": None,
                        "new_value": val_phrase,
                        "action": "ADD"
                    }]
                }

    # 2. Query Handling
    # Father / Guardian query (Evaluated FIRST before generic name query)
    if any(k in msg_normalized for k in ["father", "guardian"]):
        father = p_data.get("father_name")
        if not father and p_info and p_info.father_name:
            father = p_info.father_name
        if father and str(father).strip().lower() not in ("null", "none", "not set", ""):
            return {
                "intent": "QUERY",
                "reply": f"Your saved Father / Guardian name in your memory vault is **{father}**.",
                "updates": []
            }
        else:
            return {
                "intent": "QUERY",
                "reply": "Your Father / Guardian name is not currently saved in your memory vault. You can tell me by saying: *Save my father name as Muhammad Sarwar* to save it.",
                "updates": []
            }

    # Mother query
    if "mother" in msg_normalized:
        return {
            "intent": "QUERY",
            "reply": "Your Mother's name is not currently saved in your memory vault. You can tell me by saying: *My mother's name is ...* to save it.",
            "updates": []
        }

    # User's own Legal Name query (Strictly guarded against other entities)
    is_asking_user_name = (
        any(k in msg_normalized for k in [
            "who am i", "call me", "my name", "what is my name", "whats my name",
            "what is currently saved my name", "what is my current name", "what is my saved name",
            "my legal name", "my full name", "saved name"
        ])
        or ("name" in msg_normalized and any(w in msg_normalized for w in ["what", "who", "tell", "show", "know", "saved", "current", "my"]))
    )
    is_other_entity_name = any(w in msg_normalized for w in ["father", "mother", "guardian", "friend", "grandfather", "grandmother", "company", "boss", "mentor", "school", "college", "university", "dept", "department"])

    if is_asking_user_name and not is_other_entity_name:
        full_name = p_data.get("full_name") or user.full_name or "Muazam Ali"
        return {
            "intent": "QUERY",
            "reply": f"Your current saved legal name in your memory vault is **{full_name}**.",
            "updates": []
        }

    # Address query specifically
    if "address" in msg_normalized and any(w in msg_normalized for w in ["what", "where", "know", "saved", "current", "show", "tell", "my"]):
        addr = p_data.get("address") or "Not set"
        city = p_data.get("city") or "Not set"
        country = p_data.get("country") or "Not set"
        postal = p_data.get("postal_code") or "Not set"
        reply = (
            f"Here is your saved address in your memory vault:\n"
            f"- **Address:** {addr}\n"
            f"- **City:** {city}\n"
            f"- **Country:** {country}\n"
            f"- **Postal Code:** {postal}"
        )
        return {"intent": "QUERY", "reply": reply, "updates": []}

    # Specific Phone query
    if any(k in msg_normalized for k in ["phone", "mobile", "cell", "telephone", "contact number"]) and any(w in msg_normalized for w in ["what", "tell", "show", "know", "saved", "current", "my"]):
        phone = p_data.get("phone") or "Not set"
        return {
            "intent": "QUERY",
            "reply": f"Your saved primary phone number is **{phone}**.",
            "updates": []
        }

    # Specific Email query
    if any(k in msg_normalized for k in ["email", "mail"]) and any(w in msg_normalized for w in ["what", "tell", "show", "know", "saved", "current", "my"]):
        email = p_data.get("email") or "Not set"
        return {
            "intent": "QUERY",
            "reply": f"Your saved contact email address is **{email}**.",
            "updates": []
        }

    # Educational query
    if any(k in msg_normalized for k in ["educat", "degree", "university", "college", "school", "academ", "qualification", "graduat"]):
        degree = p_data.get("degree")
        univ = p_data.get("university")
        dept = p_data.get("department")
        grad = p_data.get("graduation_year")
        if degree or univ:
            lines = [f"Based on your verified memory vault, here are your educational details:"]
            if degree:
                lines.append(f"- **Degree:** {degree}")
            if univ:
                lines.append(f"- **Institution / University:** {univ}")
            if dept:
                lines.append(f"- **Department / Major:** {dept}")
            if grad:
                lines.append(f"- **Graduation Year:** {grad}")
            return {"intent": "QUERY", "reply": "\n".join(lines), "updates": []}
        else:
            return {
                "intent": "QUERY",
                "reply": "No educational records (degree or university) are currently saved in your memory vault. You can tell me by saying: *'I graduated with a BS in Computer Science from Stanford University'* to save it.",
                "updates": []
            }

    # General Contact query
    if any(k in msg_normalized for k in ["contact", "call", "reach"]):
        phone = p_data.get("phone") or "Not set"
        email = p_data.get("email") or "Not set"
        addr = p_data.get("address") or "Not set"
        city = p_data.get("city") or "Not set"
        reply = (
            f"Here is your saved contact information:\n"
            f"- **Primary Phone:** {phone}\n"
            f"- **Email Address:** {email}\n"
            f"- **Address:** {addr}, {city}"
        )
        return {"intent": "QUERY", "reply": reply, "updates": []}

    # Skills or Experience query
    if any(k in msg_normalized for k in ["skill", "stack", "tech"]):
        skills_found = []
        for cf in cfs:
            if "skill" in (cf.get("field_key") or "").lower():
                skills_found.append(cf.get("field_value"))
        for exp in exps:
            if exp.get("skills"):
                skills_found.append(exp.get("skills"))
        if skills_found:
            return {
                "intent": "QUERY",
                "reply": f"Your stored skills in the vault include:\n" + "\n".join([f"- {s}" for s in set(skills_found)]),
                "updates": []
            }

    if any(k in msg_normalized for k in ["work", "experience", "job", "career", "company"]):
        if exps:
            exp_lines = ["Your saved career experiences:"]
            for exp in exps:
                exp_lines.append(f"- **{exp.get('job_title')}** at **{exp.get('company')}** ({exp.get('start_date') or ''} - {exp.get('end_date') or 'Present'})")
            return {"intent": "QUERY", "reply": "\n".join(exp_lines), "updates": []}
        else:
            return {
                "intent": "QUERY",
                "reply": "You do not have any work experiences listed in your vault yet. You can paste your resume or describe your roles to save them.",
                "updates": []
            }

    # Check for matching custom fields (e.g. favorite fruit, hobby, etc.)
    for cf in cfs:
        k_norm = (cf.get("field_key") or "").lower().replace("_", " ")
        lbl_norm = (cf.get("field_label") or "").lower()
        combined_text = re.sub(r"[^a-z0-9\s]+", " ", f"{k_norm} {lbl_norm}")
        key_words = [w for w in combined_text.split() if len(w) >= 3 and w not in COPILOT_STOP_WORDS]
        if not key_words:
            continue
        if any(re.search(rf"\b{re.escape(w)}\b", msg_normalized) for w in key_words):
            return {
                "intent": "QUERY",
                "reply": f"In your memory vault, your **{cf.get('field_label') or cf.get('field_key')}** is saved as **{cf.get('field_value')}**.",
                "updates": []
            }

    # Greetings vs off-topic
    greetings = ["hi", "hello", "hey", "salam", "assalam", "greetings", "good morning", "good afternoon", "good evening", "help", "who are you", "what can you do"]
    is_greeting = any(g in msg_normalized.split() or msg_normalized.startswith(g) for g in greetings)
    if is_greeting or len(msg_normalized.split()) <= 2:
        full_name = p_data.get("full_name") or user.full_name or "there"
        return {
            "intent": "QUERY",
            "reply": f"Hello {full_name}! I am your AI Memory Copilot. You can ask me to show any detail in your memory vault (e.g. *'What is currently saved my name?'*, *'What address you know about me?'*), or command me to update your memory (e.g. *'Update my phone to 0326-8848703'* or *'My favorite fruit is mango'*).",
            "updates": []
        }

    # Off-topic or unrecognized request
    return {
        "intent": "QUERY",
        "reply": "I am your dedicated Magic Fill AI Memory Copilot. I can only assist with showing, querying, or updating your personal memory vault (such as your contact info, education, career experience, or custom saved attributes). Let me know what detail you'd like to check or update!",
        "updates": []
    }


@router.post(
    "/copilot-chat",
    response_model=APIResponse[CopilotChatResult],
    status_code=status.HTTP_200_OK,
    summary="Interactive AI Memory Copilot Chat",
    description="Conversational interface allowing users to ask questions about their stored memory or command real-time updates."
)
async def copilot_chat_endpoint(
    payload: CopilotChatRequest,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[CopilotChatResult]:
    """
    Handles conversational interactions with the user's verified memory vault.
    - Grounded Q&A (e.g., 'What are my educational experiences?')
    - Real-time updates (e.g., 'Update my name to Muazam Ali Sarwar') with DB persistence.
    """
    target_user_id = current_user.id if current_user else (payload.user_id or 1)

    # 1. Ensure user exists
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        user = User(id=target_user_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 2. Retrieve user memory vault
    profile_data = get_user_profile(db=db, user_id=target_user_id)

    def _model_to_dict(obj: Any) -> Dict[str, Any]:
        if not obj:
            return {}
        if hasattr(obj, "__table__"):
            res = {}
            for col in obj.__table__.columns:
                val = getattr(obj, col.name)
                if isinstance(val, (datetime.date, datetime.datetime)):
                    val = val.isoformat()
                res[col.name] = val
            return res
        if isinstance(obj, dict):
            return obj
        return {}

    # 3. Build sanitized profile representation for LLM
    p_info_dict = _model_to_dict(profile_data.get("personal_info"))
    exps_list = [_model_to_dict(exp) for exp in (profile_data.get("experiences") or [])]
    cfs_list = [_model_to_dict(cf) for cf in (profile_data.get("custom_fields") or [])]
    docs_list = [
        {
            "id": getattr(d, "id", None) if not isinstance(d, dict) else d.get("id"),
            "file_name": getattr(d, "file_name", None) if not isinstance(d, dict) else d.get("file_name"),
            "document_type": getattr(d, "document_type", None) if not isinstance(d, dict) else d.get("document_type"),
            "mime_type": getattr(d, "mime_type", None) if not isinstance(d, dict) else d.get("mime_type"),
            "tags": getattr(d, "tags", None) if not isinstance(d, dict) else d.get("tags")
        }
        for d in (profile_data.get("documents") or [])
    ]

    # Strip base64 blobs to keep prompt ultra-lean, fast, and prevent TPM rate-limit issues
    for k in list(p_info_dict.keys()):
        v = p_info_dict[k]
        if isinstance(v, str) and (v.startswith("data:image") or len(v) > 500):
            p_info_dict[k] = "[attached_photo]"

    for cf in cfs_list:
        v = cf.get("field_value")
        if isinstance(v, str) and (v.startswith("data:image") or len(v) > 500):
            cf["field_value"] = "[attached_document]"

    clean_profile = {
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email
        },
        "personal_info": p_info_dict,
        "experiences": exps_list,
        "custom_fields": cfs_list,
        "documents": docs_list
    }

    # 4. Construct messages for AI Provider Manager
    system_content = (
        f"{COPILOT_CHAT_SYSTEM_PROMPT}\n\n"
        f"CURRENT USER_MEMORY_VAULT JSON:\n"
        f"{json.dumps(clean_profile, indent=2, default=str)}"
    )

    llm_messages: List[Dict[str, str]] = [{"role": "system", "content": system_content}]
    if payload.history:
        for hist_msg in payload.history[-16:]:
            if hist_msg.role in ("user", "assistant") and hist_msg.content:
                # Deduplicate: if client already appended current message as last history entry, skip it
                if hist_msg.role == "user" and hist_msg.content.strip().lower() == payload.message.strip().lower():
                    continue
                llm_messages.append({"role": hist_msg.role, "content": hist_msg.content})
    llm_messages.append({"role": "user", "content": payload.message})

    # 5. Query LLM via AI Provider Manager
    parsed_res: Optional[Dict[str, Any]] = None
    try:
        parsed_res = await AIProviderManager.query_llm(
            messages=llm_messages,
            user_id=target_user_id,
            db=db,
            temperature=0.1,
            timeout_seconds=6.0,
            response_json=True
        )
    except Exception as exc:
        logger.warning("Copilot LLM query failed: %s; using local grounded fallback", exc)
        parsed_res = None

    p_info = db.query(PersonalInfo).filter(PersonalInfo.user_id == target_user_id).first()
    if not p_info:
        p_info = PersonalInfo(user_id=target_user_id, full_name=user.full_name or "Applicant")
        db.add(p_info)
        db.flush()

    if not parsed_res or not isinstance(parsed_res, dict) or "reply" not in parsed_res:
        parsed_res = _copilot_local_grounded_fallback(
            message=payload.message,
            user_profile=clean_profile,
            user=user,
            p_info=p_info,
            db=db,
            target_user_id=target_user_id,
            history=payload.history
        )

    intent = str(parsed_res.get("intent") or "QUERY").upper()
    reply = str(parsed_res.get("reply") or "").strip()
    raw_updates = parsed_res.get("updates") or []

    applied_updates: List[CopilotFieldUpdate] = []

    # 6. Apply any updates requested by user to database
    if intent == "UPDATE" or (isinstance(raw_updates, list) and len(raw_updates) > 0):
        for upd in raw_updates:
            if not isinstance(upd, dict):
                continue
            ftype = str(upd.get("field_type") or "personal_info").lower()
            raw_key = str(upd.get("key") or "").strip().lower()
            new_val = str(upd.get("new_value") or "").strip()
            label = str(upd.get("label") or raw_key.replace("_", " ").title())
            old_val = upd.get("old_value")

            if not raw_key or not new_val:
                continue

            if ftype == "personal_info":
                alias_map = {
                    "name": "full_name",
                    "applicant_name": "full_name",
                    "legal_name": "full_name",
                    "father": "father_name",
                    "father_name": "father_name",
                    "fathers_name": "father_name",
                    "guardian": "father_name",
                    "guardian_name": "father_name",
                    "mother": "mother_name",
                    "mother_name": "mother_name",
                    "phone_number": "phone",
                    "mobile": "phone",
                    "cell": "phone",
                    "telephone": "phone",
                    "contact": "phone",
                    "email_address": "email",
                    "mail": "email",
                    "residence": "address",
                    "location": "address",
                    "home_address": "address",
                    "current_address": "address",
                    "permanent_address": "address",
                    "dob": "date_of_birth",
                    "birth_date": "date_of_birth",
                    "national_id": "cnic",
                    "id_number": "cnic",
                    "college": "university",
                    "institution": "university",
                    "institute": "university",
                    "school": "university",
                    "qualification": "degree"
                }
                canon_key = alias_map.get(raw_key, raw_key)
                if canon_key == "full_name":
                    user.full_name = new_val
                    setattr(p_info, "full_name", new_val)
                elif hasattr(p_info, canon_key):
                    setattr(p_info, canon_key, new_val)
                else:
                    upsert_custom_field_by_key(
                        db=db,
                        user_id=target_user_id,
                        field_key=canon_key,
                        field_label=label,
                        field_value=new_val,
                        category="personal"
                    )

                applied_updates.append(CopilotFieldUpdate(
                    field_type="personal_info",
                    key=canon_key,
                    label=label,
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=new_val,
                    action=str(upd.get("action") or "UPDATE")
                ))

            elif ftype == "custom_field":
                upsert_custom_field_by_key(
                    db=db,
                    user_id=target_user_id,
                    field_key=raw_key,
                    field_label=label,
                    field_value=new_val,
                    category="general"
                )
                applied_updates.append(CopilotFieldUpdate(
                    field_type="custom_field",
                    key=raw_key,
                    label=label,
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=new_val,
                    action=str(upd.get("action") or "UPDATE")
                ))

            elif ftype == "experience":
                if "skill" in raw_key:
                    upsert_custom_field_by_key(
                        db=db,
                        user_id=target_user_id,
                        field_key="technical_skills",
                        field_label="Technical Skills",
                        field_value=new_val,
                        category="professional"
                    )
                applied_updates.append(CopilotFieldUpdate(
                    field_type="experience",
                    key=raw_key,
                    label=label,
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=new_val,
                    action=str(upd.get("action") or "UPDATE")
                ))

        db.commit()
        db.refresh(user)

    # 7. Fetch updated profile representation
    fresh_profile_data = get_user_profile(db=db, user_id=target_user_id)
    profile_dto = _build_profile_response(fresh_profile_data)

    return APIResponse(
        success=True,
        message="Copilot interaction processed successfully",
        data=CopilotChatResult(
            reply=reply,
            intent=intent,
            updates=applied_updates,
            updated_profile=profile_dto
        )
    )




