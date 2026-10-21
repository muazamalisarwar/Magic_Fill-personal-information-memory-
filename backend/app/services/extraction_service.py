import io
import json
import logging
import re
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.database.models import User, PersonalInfo, Experience, CustomField
from app.schemas.personal_info import PersonalInfoCreate, PersonalInfoUpdate
from app.schemas.experience import ExperienceCreate
from app.services.user_service import get_user_by_id, create_user, get_user_profile
from app.services.personal_info_service import create_personal_info, update_personal_info
from app.services.experience_service import create_experience
from app.services.custom_field_service import upsert_custom_field_by_key
from app.services.groq_service import query_groq_llm

logger = logging.getLogger("app.services.extraction_service")

EXTRACTION_SYSTEM_PROMPT = (
    "You are an expert personal profile and memory extraction assistant.\n"
    "Your objective is to read raw text, biographies, notes, or resume content and "
    "convert it into a clean, structured JSON object for personal memory storage.\n\n"
    "JSON SCHEMA REQUIREMENTS:\n"
    "Return a JSON object strictly conforming to this structure:\n"
    "{\n"
    '  "personal_info": {\n'
    '    "full_name": "USER\'S OWN full legal name (string or null). STRICT RULE: This must be the user themselves (e.g. \'My name is...\', \'I am...\'). NEVER put names of friends, references, parents, or contacts here! If no name for the user themselves is given, set null.",\n'
    '    "father_name": "Father\'s name or null",\n'
    '    "gender": "Gender (\'Male\', \'Female\', \'Other\', or null)",\n'
    '    "date_of_birth": "YYYY-MM-DD or null",\n'

    '    "cnic": "National ID / CNIC or null",\n'
    '    "phone": "User\'s primary phone number or null",\n'
    '    "email": "User\'s primary email address or null",\n'
    '    "address": "Residential address or null",\n'
    '    "city": "City or null",\n'
    '    "postal_code": "Postal code or null",\n'
    '    "country": "Country or null",\n'
    '    "university": "University or institution name or null",\n'
    '    "degree": "Degree program or null",\n'
    '    "department": "Academic department or null",\n'
    '    "semester": "Semester standing or null",\n'
    '    "registration_number": "Student registration/roll number or null"\n'
    "  },\n"
    '  "experiences": [\n'
    "    {\n"
    '      "company": "Company / Organization name (string, required)",\n'
    '      "job_title": "Position / Role (string, required)",\n'
    '      "start_date": "YYYY-MM-DD (required, if only year known use YYYY-01-01)",\n'
    '      "end_date": "YYYY-MM-DD or null if currently active/ongoing",\n'
    '      "description": "Responsibilities and accomplishments or null",\n'
    '      "skills": "Comma-separated skills used in this role or null"\n'
    "    }\n"
    "  ],\n"
    '  "custom_fields": [\n'
    "    {\n"
    '      "field_key": "Normalized snake_case identifier (e.g. friends_name, personal_mail, emergency_contact, work_email, passport_number)",\n'
    '      "field_label": "Human-readable label (e.g. Friend\'s Name, Personal Mail, Emergency Contact, Work Email)",\n'
    '      "field_value": "Extracted string value",\n'
    '      "category": "Classification category (e.g. contact, email, identity, general)"\n'
    "    }\n"
    "  ]\n"
    "}\n\n"
    "CRITICAL RULES:\n"
    "1. STRICT IDENTITY PROTECTION:\n"
    "   - personal_info is SOLELY for the primary user's personal identity.\n"
    "   - If the user provides a friend's name ('Friends Name is Taha', 'My friend is Ali'), colleague, emergency contact, or reference, NEVER assign this to personal_info.full_name!\n"
    "   - Instead, place it into custom_fields with field_key='friends_name', field_label=\"Friend's Name\", field_value='Taha', category='contact'.\n"
    "2. CUSTOM AND EXTENSIBLE FIELDS:\n"
    "   - Any attribute that does not have a dedicated slot in personal_info (such as Friend's Name, Personal Mail, Work Email, Emergency Contact, Passport Number, Github Profile, Favorite Stack, etc.) MUST be extracted into custom_fields.\n"
    "   - If the user specifies 'Personal mail is ...' or 'New email: ...', put it in custom_fields as field_key='personal_mail' and also set personal_info.email if appropriate.\n"
    "3. UPDATES AND STANDARDIZATION:\n"
    "   - Normalize field_key to snake_case (e.g. 'friends_name', 'personal_mail') so future updates to the same field can be matched and updated seamlessly.\n"
    "4. Extract ONLY facts mentioned or directly implied in the input text. Never invent details.\n"
    "5. Output must be a valid JSON object adhering strictly to the schema.\n"
)


def extract_text_from_file_bytes(content_bytes: bytes, filename: str) -> str:
    """Extract plain text from uploaded file bytes (supports PDF and plaintext/markdown)."""
    filename_lower = filename.lower()
    if filename_lower.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content_bytes))
            pages_text = []
            for page in reader.pages:
                t = page.extract_text()
                if t and t.strip():
                    pages_text.append(t.strip())
            return "\n\n".join(pages_text).strip()
        except Exception as exc:
            logger.warning("Failed to extract text from PDF %s: %s", filename, str(exc))
            return ""
    else:
        try:
            return content_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                return content_bytes.decode("latin-1", errors="ignore").strip()
            except Exception:
                return ""


def _clean_extracted_strings(data: Any) -> Any:
    """Recursively removes unnecessary backslash escapes (e.g. '\\ ' -> ' ', '\\@' -> '@', '\\+' -> '+') from LLM or parser output."""
    if isinstance(data, str):
        # Replace backslashes before spaces, punctuation, math, or special characters
        cleaned = re.sub(r'\\([ \.,@+()&/%:;!?"\'|\-\[\]\\])', r'\1', data)
        return cleaned.strip()
    elif isinstance(data, dict):
        return {k: _clean_extracted_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_clean_extracted_strings(item) for item in data]
    return data


async def extract_structured_memory_from_text(raw_text: str) -> Dict[str, Any]:
    """Uses Groq LLM to parse unstructured text into structured profile records."""
    if not raw_text or not raw_text.strip():
        return {"personal_info": None, "experiences": [], "custom_fields": []}

    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Extract structured personal memory as a JSON object from the following text:\n\n{raw_text[:8000]}"
        }
    ]

    response = await query_groq_llm(messages=messages, temperature=0.1)
    if not response or not isinstance(response, dict):
        # Fallback heuristic extraction if LLM is offline or unavailable
        raw_res = _fallback_heuristic_extraction(raw_text)
        return _clean_extracted_strings(raw_res)

    cleaned_response = _clean_extracted_strings(response)
    return {
        "personal_info": cleaned_response.get("personal_info"),
        "experiences": cleaned_response.get("experiences") or [],
        "custom_fields": cleaned_response.get("custom_fields") or [],
    }


def _fallback_heuristic_extraction(text: str) -> Dict[str, Any]:
    """Lightweight regex-based fallback extractor if LLM is unavailable."""
    clean_text = text.strip()
    custom_fields = []
    
    # Check for Friend's Name pattern
    friend_match = re.search(r"friend(?:'?s)?\s*name\s*(?:is|:)?\s*([A-Za-z\s]+)", clean_text, re.IGNORECASE)
    if friend_match:
        friend_name = friend_match.group(1).strip().split("\n")[0].strip()
        custom_fields.append({
            "field_key": "friends_name",
            "field_label": "Friend's Name",
            "field_value": friend_name,
            "category": "contact"
        })

    # Check for Personal Email / Mail pattern
    personal_mail_match = re.search(r"personal\s*(?:e?mail)\s*(?:is|:)?\s*([\w\.-]+@[\w\.-]+\.\w+)", clean_text, re.IGNORECASE)
    if personal_mail_match:
        custom_fields.append({
            "field_key": "personal_mail",
            "field_label": "Personal Mail",
            "field_value": personal_mail_match.group(1).strip(),
            "category": "email"
        })

    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", clean_text)
    phone_match = re.search(r"(\+?\d[\d\s\-]{8,}\d)", clean_text)
    gender_match = re.search(r"\b(male|female|other)\b", clean_text, re.IGNORECASE)

    # Check if text is explicitly describing the primary user's name
    user_name_match = re.search(r"(?:my\s*name\s*is|i\s*am)\s*([A-Za-z\s]{2,40})", clean_text, re.IGNORECASE)
    user_name = user_name_match.group(1).strip() if user_name_match else None

    personal_info = None
    if user_name or email_match or phone_match or gender_match:
        personal_info = {
            "full_name": user_name,
            "gender": gender_match.group(1).capitalize() if gender_match else None,
            "email": email_match.group(0) if email_match else None,
            "phone": phone_match.group(0).strip() if phone_match else None,
        }


    return {
        "personal_info": personal_info,
        "experiences": [],
        "custom_fields": custom_fields
    }


def save_extracted_memory_to_database(
    db: Session,
    user_id: int,
    extracted_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Saves or updates extracted personal information, experiences, and custom fields
    against the specified user in the relational database.
    Guarantees that third-party names (like Friend's Name) never overwrite the user's full_name.
    """
    # 1. Ensure user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 2. Process Personal Info (if any was extracted for the primary user)
    raw_pinfo = extracted_data.get("personal_info")
    if raw_pinfo and isinstance(raw_pinfo, dict):
        clean_pinfo = {k: v for k, v in raw_pinfo.items() if v is not None and str(v).strip()}
        existing_info = db.query(PersonalInfo).filter(PersonalInfo.user_id == user_id).first()

        if existing_info:
            # Partial update existing record - only update fields that were non-null
            if clean_pinfo:
                update_dto = PersonalInfoUpdate.model_validate(clean_pinfo)
                update_personal_info(db=db, user_id=user_id, info_in=update_dto)
        else:
            # Only create PersonalInfo if full_name is present
            if clean_pinfo.get("full_name"):
                create_dto = PersonalInfoCreate.model_validate(clean_pinfo)
                create_personal_info(db=db, user_id=user_id, info_in=create_dto)

    # 3. Process Experiences
    raw_experiences = extracted_data.get("experiences") or []
    for exp in raw_experiences:
        if isinstance(exp, dict) and exp.get("company") and exp.get("job_title") and exp.get("start_date"):
            try:
                exp_dto = ExperienceCreate.model_validate(exp)
                create_experience(db=db, user_id=user_id, exp_in=exp_dto)
            except Exception as exc:
                logger.warning("Could not persist experience item %s: %s", exp, str(exc))

    # 4. Process Custom & Dynamic Fields (Upsert to prevent duplicates)
    raw_custom_fields = extracted_data.get("custom_fields") or []
    for cf in raw_custom_fields:
        if isinstance(cf, dict) and cf.get("field_key") and cf.get("field_value"):
            try:
                upsert_custom_field_by_key(
                    db=db,
                    user_id=user_id,
                    field_key=cf["field_key"],
                    field_label=cf.get("field_label", cf["field_key"]),
                    field_value=str(cf["field_value"]),
                    category=cf.get("category", "general")
                )
            except Exception as exc:
                logger.warning("Could not upsert custom field %s: %s", cf, str(exc))

    # 5. Return updated full profile
    return get_user_profile(db=db, user_id=user_id)
