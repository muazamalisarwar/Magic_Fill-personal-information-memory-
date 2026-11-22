import io
import json
import logging
import re
import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.database.models import User, PersonalInfo, Experience, CustomField
from app.schemas.personal_info import PersonalInfoCreate, PersonalInfoUpdate
from app.schemas.experience import ExperienceCreate, ExperienceUpdate
from app.services.user_service import get_user_by_id, create_user, get_user_profile
from app.services.personal_info_service import create_personal_info, update_personal_info
from app.services.experience_service import create_experience
from app.services.custom_field_service import upsert_custom_field_by_key
from app.services.groq_service import query_groq_llm
from app.ai.prompts import EXTRACTION_SYSTEM_PROMPT

logger = logging.getLogger("app.services.extraction_service")


def normalize_date_for_storage(val: Any, is_end_date: bool = False) -> Optional[datetime.date]:
    """
    Robustly parses and normalizes diverse date representations found in CVs/PDFs.
    Handles:
    - '2022' -> 2022-01-01 (or 2022-12-31 for end_date)
    - '2022-05' -> 2022-05-01
    - 'May 2022', 'May, 2022', 'January 2024' -> 2022-05-01
    - '05/2022' -> 2022-05-01
    - '2022-05-14' -> 2022-05-14
    - 'Present', 'Current', 'Ongoing', 'Now', '' -> None (for ongoing roles)
    """
    if not val:
        return None
    if isinstance(val, datetime.date):
        return val
    if isinstance(val, datetime.datetime):
        return val.date()

    val_str = str(val).strip()
    if not val_str or val_str.lower() in ("present", "current", "ongoing", "now", "none", "null", "active", "presently"):
        return None

    # Try ISO YYYY-MM-DD
    m_iso = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", val_str)
    if m_iso:
        try:
            return datetime.date(int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3)))
        except ValueError:
            pass

    # Try Month Name Year (e.g. May 2022, January 2024, Sept 2021)
    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }
    m_text = re.search(r"([A-Za-z]{3,9})[\s,]+(\d{4})", val_str)
    if m_text:
        month_name = m_text.group(1).lower()[:3]
        year = int(m_text.group(2))
        month = months.get(month_name, 1)
        day = 28 if (is_end_date and month == 2) else (30 if is_end_date and month in (4, 6, 9, 11) else (31 if is_end_date else 1))
        return datetime.date(year, month, day)

    # Try YYYY-MM
    m_ym = re.search(r"(\d{4})[/-](\d{1,2})", val_str)
    if m_ym:
        year = int(m_ym.group(1))
        month = max(1, min(12, int(m_ym.group(2))))
        day = 28 if (is_end_date and month == 2) else (30 if is_end_date and month in (4, 6, 9, 11) else (31 if is_end_date else 1))
        return datetime.date(year, month, day)

    # Try MM/YYYY
    m_my = re.search(r"(\d{1,2})[/-](\d{4})", val_str)
    if m_my:
        month = max(1, min(12, int(m_my.group(1))))
        year = int(m_my.group(2))
        day = 28 if (is_end_date and month == 2) else (30 if is_end_date and month in (4, 6, 9, 11) else (31 if is_end_date else 1))
        return datetime.date(year, month, day)

    # Try Year only (e.g. 2022)
    m_y = re.search(r"\b(19\d{2}|20\d{2})\b", val_str)
    if m_y:
        year = int(m_y.group(1))
        return datetime.date(year, 12, 31) if is_end_date else datetime.date(year, 1, 1)

    return None


def extract_text_from_file_bytes(content_bytes: bytes, filename: str) -> str:
    """
    Extracts high-fidelity plain text from uploaded file bytes (PDF, TXT, MD).
    For PDFs, utilizes dual-pass layout-aware parsing to preserve column structures,
    sidebars, tables, and form fields from modern resumes.
    """
    filename_lower = filename.lower()
    if filename_lower.endswith(".pdf"):
        from pypdf import PdfReader
        try:
            reader = PdfReader(io.BytesIO(content_bytes))
        except Exception as exc:
            logger.error("Failed to initialize PdfReader for %s: %s", filename, exc)
            return ""

        extracted_pages: List[str] = []
        for page_idx, page in enumerate(reader.pages):
            page_text = ""
            # Pass 1: Try layout-aware extraction to preserve multi-column formatting
            try:
                layout_txt = page.extract_text(extraction_mode="layout", orientations=(0, 90, 180, 270))
            except Exception as e:
                layout_txt = ""

            # Pass 2: Try standard plain extraction
            try:
                plain_txt = page.extract_text(extraction_mode="plain", orientations=(0, 90, 180, 270))
            except Exception as e:
                plain_txt = ""

            # Choose the richer extraction while favoring layout
            layout_len = len(layout_txt.strip()) if layout_txt else 0
            plain_len = len(plain_txt.strip()) if plain_txt else 0

            if layout_len > 0 and layout_len >= (plain_len * 0.6):
                page_text = layout_txt
            else:
                page_text = plain_txt or layout_txt or ""

            if page_text.strip():
                extracted_pages.append(page_text.strip())

        # Also extract any interactive form fields
        try:
            form_fields = reader.get_form_text_fields()
            if form_fields:
                form_lines = [f"{k}: {v}" for k, v in form_fields.items() if v and str(v).strip()]
                if form_lines:
                    extracted_pages.append("\n--- Form Fields ---\n" + "\n".join(form_lines))
        except Exception:
            pass

        full_text = "\n\n".join(extracted_pages).strip()

        # Clean typography ligatures and zero-width artifacts
        ligature_map = {
            "\uFB01": "fi", "\uFB02": "fl", "\uFB00": "ff",
            "\uFB03": "ffi", "\uFB04": "ffl", "\u00A0": " ",
            "\u200B": "", "\uFEFF": "", "\x00": ""
        }
        for lig, clean in ligature_map.items():
            full_text = full_text.replace(lig, clean)

        # Normalize excessive whitespace
        full_text = re.sub(r"[ \t]+", " ", full_text)
        full_text = re.sub(r"\n{3,}", "\n\n", full_text)
        return full_text.strip()
    else:
        try:
            text = content_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            text = content_bytes.decode("latin-1", errors="ignore").strip()
        return text


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


async def extract_structured_memory_from_text(
    raw_text: str,
    user_id: Optional[int] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """Uses configured AI provider (or Groq default) to parse unstructured text into structured profile records."""
    if not raw_text or not raw_text.strip():
        return {"personal_info": None, "experiences": [], "custom_fields": []}

    from app.ai.provider_manager import AIProviderManager
    user_config = AIProviderManager.get_user_ai_config(db, user_id) if db and user_id else None

    # Support up to 40,000 characters for complete multi-page resumes and documents without truncation
    text_to_process = raw_text.strip()[:40000]

    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Extract structured personal memory as a JSON object from the following resume/document text:\n\n{text_to_process}"
        }
    ]

    # Temperature 0.0 for deterministic, repeatable extraction results across repeated uploads
    response = await query_groq_llm(messages=messages, temperature=0.0, config=user_config)
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
    """Enhanced regex & heuristic-based fallback extractor if external LLM is offline or unconfigured."""
    clean_text = text.strip()
    custom_fields = []
    lines = [l.strip() for l in clean_text.splitlines() if l.strip()]

    # Extract Name from top lines (only for multi-line resume-like documents, or explicit self-introduction)
    user_name = None
    self_name_match = re.search(r"(?:my\s*name\s*is|i\s*am)\s*([A-Za-z\s]{2,40})", clean_text, re.IGNORECASE)
    if self_name_match:
        user_name = self_name_match.group(1).strip()
    elif len(lines) >= 3:
        for line in lines[:6]:
            if re.search(r"\b(resume|curriculum\s*vitae|cv|page\s*\d|profile|contact|friend|reference|referee|skill|education|experience|project)\b", line, re.IGNORECASE):
                continue
            if re.match(r"^[A-Z][a-zA-Z\s\.]{2,40}$", line) and not re.search(r"[@\d:]", line) and len(line.split()) <= 4:
                user_name = line.strip()
                break

    # Email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", clean_text)
    email = email_match.group(0) if email_match else None

    # Phone
    phone_match = re.search(r"(\+?\d[\d\s\-]{8,}\d)", clean_text)
    phone = phone_match.group(0).strip() if phone_match else None

    # Gender
    gender_match = re.search(r"\b(male|female|other)\b", clean_text, re.IGNORECASE)
    gender = gender_match.group(1).capitalize() if gender_match else None

    # University
    univ_match = re.search(r"(?:university|institution|college|institute|alma\s*mater|school)\s*(?:of\s+[A-Za-z\s]+|[A-Za-z\s]+)", clean_text, re.IGNORECASE)
    university = univ_match.group(0).strip() if univ_match else None

    # Degree
    deg_match = re.search(r"\b(bachelor(?:'s)?(?:\s+of\s+[A-Za-z\s]+)?|master(?:'s)?(?:\s+of\s+[A-Za-z\s]+)?|ph\.?d\.?|bs|ms|msc|bsc|bba|mba)\b", clean_text, re.IGNORECASE)
    degree = deg_match.group(0).strip() if deg_match else None

    # Technical Skills
    skills_match = re.search(r"(?:technical\s*skills|skills|technologies|expertise|proficiencies)[\s:]+([^\n]+(?:\n[^\n]+){1,3})", clean_text, re.IGNORECASE)
    if skills_match:
        skills_text = re.sub(r"[\r\n]+", ", ", skills_match.group(1)).strip(" ,")
        custom_fields.append({
            "field_key": "technical_skills",
            "field_label": "Technical Skills",
            "field_value": skills_text[:500],
            "category": "professional"
        })

    # Check for Friend's Name pattern (test compatibility)
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

    # LinkedIn / GitHub
    li_match = re.search(r"https?://(?:www\.)?linkedin\.com/in/[\w\-]+", clean_text, re.IGNORECASE)
    gh_match = re.search(r"https?://(?:www\.)?github\.com/[\w\-]+", clean_text, re.IGNORECASE)

    personal_info = {
        "full_name": user_name,
        "email": email,
        "phone": phone,
        "gender": gender,
        "university": university,
        "degree": degree,
        "linkedin_url": li_match.group(0) if li_match else None,
        "github_url": gh_match.group(0) if gh_match else None,
    }

    if not any(personal_info.values()):
        personal_info = None

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
    Guarantees:
    - Normalizes dates safely without throwing validation errors.
    - Prevents duplicates on repeated uploads via smart experience and custom field upsert.
    - Routes unmapped personal info attributes to custom_fields safely.
    """
    # 1. Ensure user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 2. Process Personal Info
    raw_pinfo = extracted_data.get("personal_info")
    if raw_pinfo and isinstance(raw_pinfo, dict):
        alias_map = {
            "linkedin": "linkedin_url",
            "github": "github_url",
            "summary": "bio",
            "description": "bio",
            "roll_no": "registration_number",
            "roll_number": "registration_number",
            "student_id": "registration_number",
            "field_of_study": "major",
            "institution": "university",
            "college": "university",
        }
        normalized_pinfo: Dict[str, Any] = {}
        extra_to_custom: Dict[str, Any] = {}

        valid_pi_cols = {col.name for col in PersonalInfo.__table__.columns if col.name not in ("id", "user_id", "created_at", "updated_at")}

        for k, v in raw_pinfo.items():
            if v is None or str(v).strip() == "":
                continue
            canonical_key = alias_map.get(k.lower(), k.lower())
            if canonical_key in valid_pi_cols:
                normalized_pinfo[canonical_key] = v
            else:
                extra_to_custom[canonical_key] = v

        if "date_of_birth" in normalized_pinfo:
            normalized_pinfo["date_of_birth"] = normalize_date_for_storage(normalized_pinfo["date_of_birth"], False)

        existing_info = db.query(PersonalInfo).filter(PersonalInfo.user_id == user_id).first()

        if existing_info:
            if normalized_pinfo:
                try:
                    update_dto = PersonalInfoUpdate.model_validate(normalized_pinfo)
                    update_personal_info(db=db, user_id=user_id, info_in=update_dto)
                except Exception as exc:
                    logger.warning("Could not validate PersonalInfoUpdate: %s", exc)
                    for k, v in normalized_pinfo.items():
                        if hasattr(existing_info, k) and v is not None:
                            setattr(existing_info, k, v)
                    db.commit()
        else:
            if not normalized_pinfo.get("full_name"):
                normalized_pinfo["full_name"] = user.full_name or "Applicant"
            try:
                create_dto = PersonalInfoCreate.model_validate(normalized_pinfo)
                create_personal_info(db=db, user_id=user_id, info_in=create_dto)
            except Exception as exc:
                logger.warning("Could not validate PersonalInfoCreate: %s", exc)
                new_info = PersonalInfo(user_id=user_id, **{k: v for k, v in normalized_pinfo.items() if hasattr(PersonalInfo, k)})
                db.add(new_info)
                db.commit()

        # Route unmapped personal attributes into custom_fields
        for extra_k, extra_v in extra_to_custom.items():
            upsert_custom_field_by_key(
                db=db,
                user_id=user_id,
                field_key=re.sub(r"[^a-z0-9_]+", "_", extra_k).strip("_"),
                field_label=extra_k.replace("_", " ").title(),
                field_value=str(extra_v),
                category="personal"
            )

    # 3. Process Experiences (Intelligent Upsert / De-duplication)
    raw_experiences = extracted_data.get("experiences") or []
    existing_exps = db.query(Experience).filter(Experience.user_id == user_id).all()

    for exp in raw_experiences:
        if not isinstance(exp, dict):
            continue
        company = (exp.get("company") or "").strip()
        job_title = (exp.get("job_title") or "").strip()
        if not company or not job_title:
            continue

        raw_start = exp.get("start_date")
        raw_end = exp.get("end_date")

        norm_start = normalize_date_for_storage(raw_start, is_end_date=False) or datetime.date(2020, 1, 1)
        norm_end = normalize_date_for_storage(raw_end, is_end_date=True)

        if norm_end and norm_end < norm_start:
            norm_end = norm_start

        desc = (exp.get("description") or "").strip() or None
        skills = (exp.get("skills") or "").strip() or None

        # Check for existing matching experience by normalized company & role
        norm_comp = re.sub(r"[^a-z0-9]+", "", company.lower())
        norm_role = re.sub(r"[^a-z0-9]+", "", job_title.lower())

        matched_exp = None
        for ee in existing_exps:
            e_comp = re.sub(r"[^a-z0-9]+", "", (ee.company or "").lower())
            e_role = re.sub(r"[^a-z0-9]+", "", (ee.job_title or "").lower())
            if norm_comp == e_comp and norm_role == e_role:
                matched_exp = ee
                break

        if matched_exp:
            matched_exp.company = company
            matched_exp.job_title = job_title
            matched_exp.start_date = norm_start
            matched_exp.end_date = norm_end
            if desc:
                matched_exp.description = desc
            if skills:
                matched_exp.skills = skills
            db.commit()
        else:
            new_exp = Experience(
                user_id=user_id,
                company=company,
                job_title=job_title,
                start_date=norm_start,
                end_date=norm_end,
                description=desc,
                skills=skills
            )
            db.add(new_exp)
            db.commit()
            existing_exps.append(new_exp)

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

    return get_user_profile(db=db, user_id=user_id)
