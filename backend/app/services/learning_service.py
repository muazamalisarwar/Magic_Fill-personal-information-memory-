import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.database.models import User, PersonalInfo, CustomField, Experience
from app.schemas.learning import (
    FieldCategory,
    LearningActionType,
    EvaluateFieldRequest,
    EvaluateFieldResponse,
    CommitLearningRequest,
    CommitLearningResponse,
)
from app.services.custom_field_service import upsert_custom_field_by_key
from app.services.personal_info_service import update_personal_info, create_personal_info
from app.schemas.personal_info import PersonalInfoUpdate, PersonalInfoCreate
from app.services.user_service import get_user_profile
from app.services.groq_service import query_groq_llm

logger = logging.getLogger("app.services.learning_service")


# ---------------------------------------------------------------------------
# Semantic Normalization & Equivalent Dictionaries
# ---------------------------------------------------------------------------

SEMANTIC_CANONICAL_MAP = {
    # Social & Professional URLs
    "linkedin": ("linkedin_url", "LinkedIn Profile URL", FieldCategory.PROFESSIONAL_INFO, "social"),
    "linkedin_url": ("linkedin_url", "LinkedIn Profile URL", FieldCategory.PROFESSIONAL_INFO, "social"),
    "linkedin_profile": ("linkedin_url", "LinkedIn Profile URL", FieldCategory.PROFESSIONAL_INFO, "social"),
    "linkedin_profile_url": ("linkedin_url", "LinkedIn Profile URL", FieldCategory.PROFESSIONAL_INFO, "social"),
    "github": ("github_url", "GitHub Profile URL", FieldCategory.PROFESSIONAL_INFO, "social"),
    "github_url": ("github_url", "GitHub Profile URL", FieldCategory.PROFESSIONAL_INFO, "social"),
    "github_profile": ("github_url", "GitHub Profile URL", FieldCategory.PROFESSIONAL_INFO, "social"),
    "portfolio": ("portfolio_url", "Portfolio URL", FieldCategory.PROFESSIONAL_INFO, "portfolio"),
    "portfolio_url": ("portfolio_url", "Portfolio URL", FieldCategory.PROFESSIONAL_INFO, "portfolio"),
    "portfolio_link": ("portfolio_url", "Portfolio URL", FieldCategory.PROFESSIONAL_INFO, "portfolio"),
    "portfolio_website": ("portfolio_url", "Portfolio URL", FieldCategory.PROFESSIONAL_INFO, "portfolio"),
    "personal_website": ("portfolio_url", "Personal Website", FieldCategory.PROFESSIONAL_INFO, "portfolio"),
    "website": ("portfolio_url", "Personal Website", FieldCategory.PROFESSIONAL_INFO, "portfolio"),
    "website_url": ("portfolio_url", "Personal Website", FieldCategory.PROFESSIONAL_INFO, "portfolio"),

    # Professional & Career
    "certifications": ("certifications", "Certifications", FieldCategory.PROFESSIONAL_INFO, "professional"),
    "certification": ("certifications", "Certifications", FieldCategory.PROFESSIONAL_INFO, "professional"),
    "certificates": ("certifications", "Certifications", FieldCategory.PROFESSIONAL_INFO, "professional"),
    "license": ("certifications", "License / Certification", FieldCategory.PROFESSIONAL_INFO, "professional"),
    "salary": ("salary", "Salary / Compensation", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "monthly_salary": ("salary", "Monthly Salary", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "current_salary": ("salary", "Current Salary", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "expected_salary": ("salary", "Expected Salary", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "compensation": ("salary", "Salary / Compensation", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "skills": ("skills", "Technical Skills", FieldCategory.PROFESSIONAL_INFO, "professional"),
    "technical_skills": ("skills", "Technical Skills", FieldCategory.PROFESSIONAL_INFO, "professional"),
    "years_of_experience": ("years_of_experience", "Years of Experience", FieldCategory.PROFESSIONAL_INFO, "professional"),
    "work_authorization": ("work_authorization", "Work Authorization", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "notice_period": ("notice_period", "Notice Period", FieldCategory.PROFESSIONAL_INFO, "employment"),

    # Personal Contacts
    "emergency_contact": ("emergency_contact", "Emergency Contact", FieldCategory.PERSONAL_INFO, "emergency"),
    "emergency_phone": ("emergency_contact", "Emergency Contact Phone", FieldCategory.PERSONAL_INFO, "emergency"),
    "emergency_contact_number": ("emergency_contact", "Emergency Contact Phone", FieldCategory.PERSONAL_INFO, "emergency"),
    "emergency_contact_name": ("emergency_contact_name", "Emergency Contact Name", FieldCategory.PERSONAL_INFO, "emergency"),
    "phone": ("phone", "Phone Number", FieldCategory.PERSONAL_INFO, "contact"),
    "mobile": ("phone", "Mobile Number", FieldCategory.PERSONAL_INFO, "contact"),
    "phone_number": ("phone", "Phone Number", FieldCategory.PERSONAL_INFO, "contact"),
    "contact_number": ("phone", "Contact Number", FieldCategory.PERSONAL_INFO, "contact"),
    "cell_number": ("phone", "Cell Number", FieldCategory.PERSONAL_INFO, "contact"),
    "telephone": ("phone", "Telephone", FieldCategory.PERSONAL_INFO, "contact"),
    "email": ("email", "Email Address", FieldCategory.PERSONAL_INFO, "contact"),
    "email_address": ("email", "Email Address", FieldCategory.PERSONAL_INFO, "contact"),
    "personal_email": ("email", "Personal Email", FieldCategory.PERSONAL_INFO, "contact"),

    # Personal Details
    "full_name": ("full_name", "Full Name", FieldCategory.PERSONAL_INFO, "personal"),
    "name": ("full_name", "Full Name", FieldCategory.PERSONAL_INFO, "personal"),
    "your_name": ("full_name", "Full Name", FieldCategory.PERSONAL_INFO, "personal"),
    "applicant_name": ("full_name", "Full Name", FieldCategory.PERSONAL_INFO, "personal"),
    "legal_name": ("full_name", "Full Name", FieldCategory.PERSONAL_INFO, "personal"),
    "candidate_name": ("full_name", "Full Name", FieldCategory.PERSONAL_INFO, "personal"),
    "name_of_applicant": ("full_name", "Full Name", FieldCategory.PERSONAL_INFO, "personal"),
    "first_name": ("first_name", "First Name", FieldCategory.PERSONAL_INFO, "personal"),
    "last_name": ("last_name", "Last Name", FieldCategory.PERSONAL_INFO, "personal"),
    "father_name": ("father_name", "Father's Name", FieldCategory.PERSONAL_INFO, "personal"),
    "fathers_name": ("father_name", "Father's Name", FieldCategory.PERSONAL_INFO, "personal"),
    "father": ("father_name", "Father's Name", FieldCategory.PERSONAL_INFO, "personal"),
    "father_guardian_name": ("father_name", "Father / Guardian Name", FieldCategory.PERSONAL_INFO, "personal"),
    "parent_guardian_name": ("father_name", "Father / Guardian Name", FieldCategory.PERSONAL_INFO, "personal"),
    "father_guardian": ("father_name", "Father / Guardian Name", FieldCategory.PERSONAL_INFO, "personal"),
    "parent_guardian": ("father_name", "Father / Guardian Name", FieldCategory.PERSONAL_INFO, "personal"),
    "guardian_name": ("father_name", "Guardian's Name", FieldCategory.PERSONAL_INFO, "personal"),
    "guardian": ("father_name", "Guardian's Name", FieldCategory.PERSONAL_INFO, "personal"),
    "parent_name": ("father_name", "Parent's Name", FieldCategory.PERSONAL_INFO, "personal"),
    "parent": ("father_name", "Parent's Name", FieldCategory.PERSONAL_INFO, "personal"),
    "mother_name": ("mother_name", "Mother's Name", FieldCategory.PERSONAL_INFO, "personal"),
    "mothers_name": ("mother_name", "Mother's Name", FieldCategory.PERSONAL_INFO, "personal"),
    "mother": ("mother_name", "Mother's Name", FieldCategory.PERSONAL_INFO, "personal"),
    "spouse_name": ("spouse_name", "Spouse's Name", FieldCategory.PERSONAL_INFO, "personal"),
    "date_of_birth": ("date_of_birth", "Date of Birth", FieldCategory.PERSONAL_INFO, "personal"),
    "dob": ("date_of_birth", "Date of Birth", FieldCategory.PERSONAL_INFO, "personal"),
    "cnic": ("cnic", "CNIC / National ID", FieldCategory.PERSONAL_INFO, "identity"),
    "national_id": ("cnic", "National ID / CNIC", FieldCategory.PERSONAL_INFO, "identity"),
    "gender": ("gender", "Gender", FieldCategory.PERSONAL_INFO, "personal"),
    "bio": ("bio", "Biography / Summary", FieldCategory.PROFESSIONAL_INFO, "professional"),
    "summary": ("bio", "Professional Summary", FieldCategory.PROFESSIONAL_INFO, "professional"),
    "professional_summary": ("bio", "Professional Summary", FieldCategory.PROFESSIONAL_INFO, "professional"),
    "about_me": ("bio", "About Me", FieldCategory.PERSONAL_INFO, "personal"),
    "about_yourself": ("bio", "About Me", FieldCategory.PERSONAL_INFO, "personal"),
    "relocation": ("relocation", "Willing to Relocate", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "willing_to_relocate": ("relocation", "Willing to Relocate", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "open_to_relocation": ("relocation", "Willing to Relocate", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "gpa": ("gpa", "Grade Point Average (GPA)", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "grade_point_average": ("gpa", "Grade Point Average (GPA)", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "graduation_date": ("graduation_date", "Graduation Date", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "grad_date": ("graduation_date", "Graduation Date", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "completion_date": ("graduation_date", "Graduation Date", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "start_date": ("start_date", "Available Start Date", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "available_date": ("start_date", "Available Start Date", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "earliest_start_date": ("start_date", "Available Start Date", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "availability": ("start_date", "Availability / Start Date", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "authorized_to_work": ("work_authorization", "Work Authorization", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "legally_authorized": ("work_authorization", "Work Authorization", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "work_eligibility": ("work_authorization", "Work Authorization", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "experience_years": ("years_of_experience", "Years of Experience", FieldCategory.PROFESSIONAL_INFO, "professional"),
    "total_experience": ("years_of_experience", "Years of Experience", FieldCategory.PROFESSIONAL_INFO, "professional"),
    "exp_years": ("years_of_experience", "Years of Experience", FieldCategory.PROFESSIONAL_INFO, "professional"),
    "years_experience": ("years_of_experience", "Years of Experience", FieldCategory.PROFESSIONAL_INFO, "professional"),

    # Addresses
    "address": ("address", "Residential Address", FieldCategory.PERSONAL_INFO, "address"),
    "street_address": ("address", "Street Address", FieldCategory.PERSONAL_INFO, "address"),
    "city": ("city", "City", FieldCategory.PERSONAL_INFO, "address"),
    "postal_code": ("postal_code", "Postal / ZIP Code", FieldCategory.PERSONAL_INFO, "address"),
    "zip_code": ("postal_code", "Postal / ZIP Code", FieldCategory.PERSONAL_INFO, "address"),
    "zip": ("postal_code", "Postal / ZIP Code", FieldCategory.PERSONAL_INFO, "address"),
    "country": ("country", "Country", FieldCategory.PERSONAL_INFO, "address"),
    "nationality": ("country", "Nationality / Country", FieldCategory.PERSONAL_INFO, "address"),

    # Academic
    "university": ("university", "University / Institution", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "university_name": ("university", "University / Institution", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "institution": ("university", "Institution / University", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "alma_mater": ("university", "Alma Mater", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "college": ("university", "College / Institution", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "school": ("university", "School / Institution", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "degree": ("degree", "Degree", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "degree_name": ("degree", "Degree", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "qualification": ("degree", "Highest Qualification", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "highest_qualification": ("degree", "Highest Qualification", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "highest_degree": ("degree", "Highest Degree", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "education_level": ("degree", "Education Level", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "current_degree": ("degree", "Current Degree", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "major": ("major", "Major / Field of Study", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "field_of_study": ("major", "Field of Study", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "discipline": ("major", "Discipline / Major", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "department": ("department", "Academic Department", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "graduation_year": ("graduation_year", "Graduation Year", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "semester": ("semester", "Semester", FieldCategory.PROFESSIONAL_INFO, "academic"),
    "registration_number": ("registration_number", "Registration Number", FieldCategory.PROFESSIONAL_INFO, "academic"),

    # Employment
    "job_title": ("job_title", "Job Title / Designation", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "designation": ("job_title", "Designation", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "role": ("job_title", "Job Role", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "desired_role": ("job_title", "Desired Role", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "position": ("job_title", "Position Applied For", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "company": ("company", "Company / Employer", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "employer": ("company", "Current Employer", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "expected_ctc": ("salary", "Expected Compensation", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "current_ctc": ("salary", "Current Compensation", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "desired_salary": ("salary", "Desired Salary", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "remote": ("remote_preference", "Remote Preference", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "work_mode": ("remote_preference", "Work Mode Preference", FieldCategory.PROFESSIONAL_INFO, "employment"),
    "marital_status": ("marital_status", "Marital Status", FieldCategory.PERSONAL_INFO, "personal"),
    "blood_group": ("blood_group", "Blood Group", FieldCategory.PERSONAL_INFO, "personal"),
    "religion": ("religion", "Religion", FieldCategory.PERSONAL_INFO, "personal"),
    "domicile": ("domicile", "Domicile / District", FieldCategory.PERSONAL_INFO, "address"),
    "province": ("province", "Province / State", FieldCategory.PERSONAL_INFO, "address"),
    "state": ("province", "State / Province", FieldCategory.PERSONAL_INFO, "address"),
    "current_location": ("city", "Current City / Location", FieldCategory.PERSONAL_INFO, "address"),
    "location": ("city", "Location / City", FieldCategory.PERSONAL_INFO, "address"),
}


def _normalize_identifier(text: Optional[str]) -> str:
    """Normalize text into lower snake_case."""
    if not text:
        return ""
    cleaned = re.sub(r"[_\-\.\s]+", "_", text.strip().lower())
    cleaned = re.sub(r"[^a-z0-9_]", "", cleaned)
    return cleaned.strip("_")


def _normalize_value_for_comparison(val: str, key_type: str = "") -> str:
    """Normalizes string values for accurate duplicate and semantic comparison."""
    if not val:
        return ""
    v = val.strip().lower()

    # URL normalization (strip protocol, www, and trailing slashes)
    if "url" in key_type or "link" in key_type or "website" in key_type or v.startswith("http") or "linkedin.com" in v or "github.com" in v:
        v = re.sub(r"^https?://", "", v)
        v = re.sub(r"^www\.", "", v)
        v = v.rstrip("/")
        return v

    # Phone normalization (keep only digits)
    if "phone" in key_type or "mobile" in key_type or "contact" in key_type:
        digits = re.sub(r"\D", "", v)
        # Compare last 10 digits to match with/without country codes (e.g. +92 300 1234567 vs 0300 1234567)
        return digits[-10:] if len(digits) >= 10 else digits

    # Email normalization
    if "email" in key_type or "@" in v:
        return v.strip().lower()

    # General text: remove excessive spaces and punctuation
    v = re.sub(r"\s+", " ", v)
    return v


# ---------------------------------------------------------------------------
# Layer 1 & 2: Deterministic Classification System
# ---------------------------------------------------------------------------

def classify_field_deterministically(
    field_name: Optional[str],
    label: Optional[str],
    value: str,
    input_type: Optional[str] = "text",
    placeholder: Optional[str] = None
) -> Tuple[FieldCategory, Optional[str], Optional[str], Optional[str]]:
    """
    Classifies a form field into one of the 6 defined categories:
    - PERSONAL_INFO
    - PROFESSIONAL_INFO
    - COMMUNICATION_CONTENT
    - TRANSACTIONAL
    - SENSITIVE_OR_SECRET
    - UNKNOWN

    Returns: (category, canonical_key, human_label, custom_field_category)
    """
    val = (value or "").strip()
    norm_type = (input_type or "text").lower()
    combined_desc = f"{field_name or ''} {label or ''} {placeholder or ''}".lower()
    norm_id = _normalize_identifier(field_name or "")
    norm_lbl = _normalize_identifier(label or "")

    # 1. Reject empty, minimal (unless numeric/digit), or placeholder values
    if not val or (len(val) < 2 and not val.isdigit()) or val.lower() in ("n/a", "none", "test", "placeholder", "undefined", "null"):
        return FieldCategory.UNKNOWN, None, None, None

    # 2. Check SENSITIVE_OR_SECRET
    if norm_type in ("password", "hidden"):
        return FieldCategory.SENSITIVE_OR_SECRET, None, None, None

    sensitive_keywords = [
        "password", "passcode", "pin", "cvv", "cvc", "security code", "card number",
        "credit card", "debit card", "cardholder", "exp date", "expiration date",
        "expiry", "billing zip", "otp", "one time password", "2fa", "mfa",
        "verification code", "auth code", "token", "secret", "captcha", "recaptcha"
    ]
    if any(k in combined_desc for k in sensitive_keywords):
        return FieldCategory.SENSITIVE_OR_SECRET, None, None, None

    # 3. Check COMMUNICATION_CONTENT (Chat, comments, message boxes, support, reviews)
    comm_keywords = [
        "chat", "prompt", "message", "comment", "discussion", "reply", "review",
        "feedback", "complaint", "inquiry", "support", "ticket", "ask a question",
        "how can we help", "body", "email body", "email content", "tweet",
        "post content", "forum", "subject line", "tell us more", "leave a note",
        "write a comment", "type a message", "what is this document", "describe what this",
        "document description", "photo description", "media description", "ai description",
        "doc_desc", "media_description", "file description"
    ]
    if any(k in combined_desc for k in comm_keywords):
        return FieldCategory.COMMUNICATION_CONTENT, None, None, None

    # Multi-line free form communication text
    if norm_type == "textarea" and (len(val) > 120 or "\n" in val):
        # Unless it specifically has an explicit label like "Residential Address"
        if not any(k in combined_desc for k in ["address", "street", "bio", "summary", "about me"]):
            return FieldCategory.COMMUNICATION_CONTENT, None, None, None

    # Chat sentences heuristic
    conversational_signals = ["hello", "hi there", "please help", "i wanted to ask", "thank you", "thanks", "problem with", "issue with", "this is my", "this is a"]
    if any(sig in val.lower() for sig in conversational_signals) and len(val.split()) > 3:
        return FieldCategory.COMMUNICATION_CONTENT, None, None, None

    # 4. Check TRANSACTIONAL (Coupons, orders, bookings, tracking, quantities)
    trans_keywords = [
        "coupon", "promo", "promo code", "discount code", "voucher", "order number",
        "order id", "invoice", "receipt", "tracking number", "shipment number",
        "booking id", "flight number", "hotel reservation", "ticket number",
        "quantity", "qty", "delivery note", "special instruction", "drop off note",
        "gate code", "donation amount", "tip amount", "item count", "search", "query",
        "filter", "find"
    ]
    if any(k in combined_desc for k in trans_keywords):
        return FieldCategory.TRANSACTIONAL, None, None, None

    # 5. Check Semantic Canonical Dictionary for Matches
    def _validate_candidate_value(k: str, v: str) -> bool:
        """Ensures that detected canonical key matches the shape of the user-entered value."""
        if k in ("full_name", "first_name", "last_name"):
            # A field like "Father Name", "Guardian Name", "Mother Name", "Spouse Name", "Emergency Contact", "Degree Name", etc. is NOT the user's name
            if any(tok in combined_desc for tok in [
                "father", "guardian", "parent", "mother", "spouse", "emergency", "reference", "referee", "nominee",
                "degree", "university", "college", "school", "institution", "company", "employer",
                "department", "program", "course", "subject", "file", "document", "photo"
            ]):
                return False
        if k in ("cnic", "national_id"):
            # National IDs are numbers/hyphens (e.g. 35405-0542380-2 or 3540505423802).
            # A text sentence like "This is my official profile photo" can NEVER be a CNIC.
            digits_only = re.sub(r"\D", "", v)
            has_multiple_words = len([w for w in v.split() if w.isalpha() and len(w) > 2]) >= 2
            if has_multiple_words or len(digits_only) < 7:
                return False
        return True

    # Test normalized key directly
    for probe in [norm_lbl, norm_id]:
        if probe in SEMANTIC_CANONICAL_MAP:
            canon_k, human_l, cat, sub_cat = SEMANTIC_CANONICAL_MAP[probe]
            if _validate_candidate_value(canon_k, val):
                return cat, canon_k, human_l, sub_cat

    # Substring dictionary lookup with word-boundary and validation (sorted by key length descending so longer specific keys like 'father_name' or 'parent_guardian_name' match before 'name')
    sorted_synonyms = sorted(SEMANTIC_CANONICAL_MAP.items(), key=lambda item: len(item[0]), reverse=True)
    for syn, (canon_k, human_l, cat, sub_cat) in sorted_synonyms:
        syn_word = syn.replace("_", " ")
        if re.search(rf"\b{re.escape(syn_word)}\b", combined_desc) or re.search(rf"\b{re.escape(syn)}\b", combined_desc):
            if _validate_candidate_value(canon_k, val):
                return cat, canon_k, human_l, sub_cat

    # 6. Specific Domain Heuristics
    # LinkedIn URL
    if "linkedin.com" in val.lower() or "linkedin" in combined_desc:
        return FieldCategory.PROFESSIONAL_INFO, "linkedin_url", "LinkedIn Profile URL", "social"

    # GitHub URL
    if "github.com" in val.lower() or "github" in combined_desc:
        return FieldCategory.PROFESSIONAL_INFO, "github_url", "GitHub Profile URL", "social"

    # Portfolio / Website URL
    if (val.lower().startswith("http://") or val.lower().startswith("https://")) and any(k in combined_desc for k in ["portfolio", "website", "site", "web"]):
        return FieldCategory.PROFESSIONAL_INFO, "portfolio_url", "Portfolio URL", "portfolio"

    # Email
    if re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", val):
        return FieldCategory.PERSONAL_INFO, "email", "Email Address", "contact"

    # Phone
    if re.match(r"^\+?[\d\s\-]{8,20}$", val) and any(k in combined_desc for k in ["phone", "mobile", "cell", "tel", "contact", "call"]):
        return FieldCategory.PERSONAL_INFO, "phone", "Phone Number", "contact"

    # If purpose cannot be confidently identified, default to UNKNOWN
    return FieldCategory.UNKNOWN, None, None, None


# ---------------------------------------------------------------------------
# Layer 3: Contextual LLM Classification for Ambiguous Fields
# ---------------------------------------------------------------------------

async def classify_field_with_groq_llm(
    field_name: Optional[str],
    label: Optional[str],
    value: str,
    form_context: Optional[str] = None
) -> Tuple[FieldCategory, Optional[str], Optional[str]]:
    """
    Uses Groq LLM to contextually evaluate an ambiguous field on a job application
    or profile form. Strictly defaults to UNKNOWN if uncertainty exists.
    """
    system_prompt = (
        "You are Magic Fill's Intelligent Field Classifier.\n"
        "Your task is to classify a single form input field and value into exactly one category:\n"
        "- PERSONAL_INFO: Reusable personal profile attribute (name, email, phone, address, DOB, emergency contact)\n"
        "- PROFESSIONAL_INFO: Reusable career/education profile attribute (LinkedIn, GitHub, portfolio, degree, skills, certifications, salary)\n"
        "- COMMUNICATION_CONTENT: Free-form text, chat message, comment, feedback, inquiry, or discussion\n"
        "- TRANSACTIONAL: One-time order, booking, coupon, tracking, or application-specific answer\n"
        "- SENSITIVE_OR_SECRET: Password, PIN, OTP, payment credential, or secret\n"
        "- UNKNOWN: Ambiguous, uncertain, or generic field\n\n"
        "STRICT RULE: Only classify as PERSONAL_INFO or PROFESSIONAL_INFO if the field is genuinely a reusable personal/professional profile attribute.\n"
        "Output JSON only: {\"category\": \"...\", \"canonical_key\": \"snake_case_key\", \"field_label\": \"Human Readable Title\"}"
    )

    user_prompt = {
        "field_name": field_name,
        "label": label,
        "value": value[:200],
        "form_context": form_context or "Web Form"
    }

    try:
        import json
        res = await query_groq_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt)}
            ],
            temperature=0.1
        )
        if res and isinstance(res, dict) and "category" in res:
            cat_str = str(res["category"]).strip().upper()
            try:
                cat = FieldCategory(cat_str)
                canon_k = _normalize_identifier(res.get("canonical_key") or label or field_name)
                f_label = res.get("field_label") or label or canon_k.replace("_", " ").title()
                return cat, canon_k, f_label
            except Exception:
                pass
    except Exception as e:
        logger.warning("Groq classification fallback error: %s", str(e))

    return FieldCategory.UNKNOWN, None, None


# ---------------------------------------------------------------------------
# Core Memory Comparison & Duplicate Detection Engine
# ---------------------------------------------------------------------------

async def evaluate_field_for_learning(
    db: Session,
    user_id: int,
    request: EvaluateFieldRequest
) -> EvaluateFieldResponse:
    """
    Evaluates whether a field completed by a user should trigger a memory save/update suggestion.
    1. Classifies the field (PERSONAL_INFO, PROFESSIONAL_INFO, or excluded categories).
    2. Compares against the user's existing records in the database.
    3. Detects if identical value is already saved (NO_ACTION).
    4. Detects if attribute exists with a different value (UPDATE_ATTRIBUTE).
    5. Detects if attribute is genuinely new (NEW_ATTRIBUTE).
    """
    val = request.value.strip()

    # Step 1: Deterministic Classification
    category, canon_key, field_lbl, custom_cat = classify_field_deterministically(
        field_name=request.field_name,
        label=request.label,
        value=val,
        input_type=request.input_type,
        placeholder=request.placeholder
    )

    # Step 2: Contextual AI Classification if deterministic returned UNKNOWN
    if category == FieldCategory.UNKNOWN and request.label and len(request.label.strip()) > 3:
        try:
            category, canon_key, field_lbl = await classify_field_with_groq_llm(
                field_name=request.field_name,
                label=request.label,
                value=val,
                form_context=request.form_context
            )
        except Exception as e:
            logger.warning("Groq classification fallback encountered error: %s", str(e))
            category = FieldCategory.UNKNOWN

    # Step 2b: Resilient Fallback for Application / Profile Form Questions
    # If not explicitly marked as sensitive, chat, or transactional, treat any non-empty
    # labeled form field as a learnable personal or professional attribute.
    if category == FieldCategory.UNKNOWN:
        desc = (request.label or request.field_name or "").strip()
        if desc and len(desc) >= 2:
            generic_placeholders = ["your answer", "short answer", "long answer", "type here", "enter text", "null", "undefined"]
            if not any(gp in desc.lower() for gp in generic_placeholders):
                prof_signals = [
                    "experience", "salary", "skill", "job", "work", "role", "degree",
                    "university", "school", "college", "academic", "career", "tech",
                    "code", "portfolio", "github", "linkedin", "notice", "relocat",
                    "qualification", "department", "semester", "gpa", "major", "title",
                    "position", "framework", "language", "certificate", "license"
                ]
                if any(s in desc.lower() for s in prof_signals):
                    category = FieldCategory.PROFESSIONAL_INFO
                else:
                    category = FieldCategory.PERSONAL_INFO
                canon_key = _normalize_identifier(desc)
                field_lbl = desc.replace("_", " ").strip().title()

    # Step 3: Enforce that ONLY PERSONAL_INFO and PROFESSIONAL_INFO qualify for suggestions!
    if category not in (FieldCategory.PERSONAL_INFO, FieldCategory.PROFESSIONAL_INFO):
        return EvaluateFieldResponse(
            category=category,
            is_learnable=False,
            action_type=LearningActionType.NO_ACTION,
            reason=f"Field category '{category.value}' is excluded from personal memory learning."
        )

    if not canon_key:
        canon_key = _normalize_identifier(request.label or request.field_name or "custom_attribute")
    if not field_lbl:
        field_lbl = (request.label or canon_key.replace("_", " ").title()).strip()

    # Step 4: Compare against existing user memory in DB
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return EvaluateFieldResponse(
            category=category,
            is_learnable=False,
            action_type=LearningActionType.NO_ACTION,
            reason="User not found"
        )

    personal_info = user.personal_info
    custom_fields: List[CustomField] = user.custom_fields or []
    experiences: List[Experience] = user.experiences or []

    # 4a. Check PersonalInfo columns
    pinfo_map = {
        "full_name": personal_info.full_name if personal_info else None,
        "first_name": (personal_info.full_name.split()[0] if personal_info and personal_info.full_name else None),
        "last_name": (personal_info.full_name.split()[-1] if personal_info and personal_info.full_name and len(personal_info.full_name.split()) > 1 else None),
        "email": personal_info.email if personal_info else None,
        "phone": personal_info.phone if personal_info else None,
        "date_of_birth": (personal_info.date_of_birth.isoformat() if personal_info and personal_info.date_of_birth else None),
        "gender": personal_info.gender if personal_info else None,
        "cnic": personal_info.cnic if personal_info else None,
        "address": personal_info.address if personal_info else None,
        "city": personal_info.city if personal_info else None,
        "postal_code": personal_info.postal_code if personal_info else None,
        "country": personal_info.country if personal_info else None,
        "university": personal_info.university if personal_info else None,
        "degree": personal_info.degree if personal_info else None,
        "department": personal_info.department if personal_info else None,
        "father_name": personal_info.father_name if personal_info else None,
    }

    if canon_key in pinfo_map and pinfo_map[canon_key]:
        existing_val = str(pinfo_map[canon_key]).strip()
        norm_existing = _normalize_value_for_comparison(existing_val, canon_key)
        norm_new = _normalize_value_for_comparison(val, canon_key)

        if norm_existing == norm_new:
            # Exact or semantic duplicate already in memory
            return EvaluateFieldResponse(
                category=category,
                is_learnable=False,
                action_type=LearningActionType.NO_ACTION,
                canonical_key=canon_key,
                field_label=field_lbl,
                existing_value=existing_val,
                reason=f"Value for '{field_lbl}' is already saved in personal memory."
            )
        else:
            # Existing attribute has a different value -> UPDATE suggestion!
            return EvaluateFieldResponse(
                category=category,
                is_learnable=True,
                action_type=LearningActionType.UPDATE_ATTRIBUTE,
                canonical_key=canon_key,
                field_label=field_lbl,
                existing_value=existing_val,
                new_value=val,
                reason=f"Your saved {field_lbl} is different from the value entered."
            )

    # 4b. Check Custom Fields
    matched_cf = None
    for cf in custom_fields:
        cf_key = _normalize_identifier(cf.field_key)
        cf_lbl = _normalize_identifier(cf.field_label)
        if cf_key == canon_key or cf_lbl == canon_key or cf_lbl == _normalize_identifier(field_lbl):
            matched_cf = cf
            break
        # Also match semantic groups like linkedin / linkedin_url
        if "linkedin" in canon_key and "linkedin" in cf_key:
            matched_cf = cf
            break
        if "github" in canon_key and "github" in cf_key:
            matched_cf = cf
            break
        if "portfolio" in canon_key and "portfolio" in cf_key:
            matched_cf = cf
            break

    if matched_cf:
        existing_val = str(matched_cf.field_value).strip()
        norm_existing = _normalize_value_for_comparison(existing_val, canon_key)
        norm_new = _normalize_value_for_comparison(val, canon_key)

        if norm_existing == norm_new:
            return EvaluateFieldResponse(
                category=category,
                is_learnable=False,
                action_type=LearningActionType.NO_ACTION,
                canonical_key=canon_key,
                field_label=matched_cf.field_label,
                existing_value=existing_val,
                reason=f"Value for '{matched_cf.field_label}' is already saved in custom memory."
            )
        else:
            return EvaluateFieldResponse(
                category=category,
                is_learnable=True,
                action_type=LearningActionType.UPDATE_ATTRIBUTE,
                canonical_key=canon_key,
                field_label=matched_cf.field_label,
                existing_value=existing_val,
                new_value=val,
                reason=f"Your saved {matched_cf.field_label} is different from the value entered."
            )

    # 4c. Check Experiences (job title / company)
    if canon_key in ("job_title", "company") and experiences:
        latest_exp = experiences[0]
        exp_val = latest_exp.job_title if canon_key == "job_title" else latest_exp.company
        if exp_val:
            norm_existing = _normalize_value_for_comparison(exp_val, canon_key)
            norm_new = _normalize_value_for_comparison(val, canon_key)
            if norm_existing == norm_new:
                return EvaluateFieldResponse(
                    category=category,
                    is_learnable=False,
                    action_type=LearningActionType.NO_ACTION,
                    canonical_key=canon_key,
                    field_label=field_lbl,
                    existing_value=exp_val,
                    reason=f"Value for '{field_lbl}' is already recorded in work experiences."
                )

    # Step 5: Attribute is genuinely new!
    return EvaluateFieldResponse(
        category=category,
        is_learnable=True,
        action_type=LearningActionType.NEW_ATTRIBUTE,
        canonical_key=canon_key,
        field_label=field_lbl,
        new_value=val,
        reason=f"Magic Fill detected a new {category.value.lower().replace('_', ' ')} attribute: {field_lbl}"
    )


# ---------------------------------------------------------------------------
# Commit Approved Learning to Database
# ---------------------------------------------------------------------------

def commit_learned_field(
    db: Session,
    user_id: int,
    request: CommitLearningRequest
) -> CommitLearningResponse:
    """
    Saves or updates the user-approved attribute into the database.
    Integrates directly with personal_info or custom_fields tables.
    """
    canon_k = _normalize_identifier(request.canonical_key)
    f_lbl = request.field_label.strip()
    val = request.value.strip()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return CommitLearningResponse(
            saved=False,
            message="User not found",
            canonical_key=canon_k,
            action_taken="NONE"
        )

    # 1. Check if attribute belongs to standard PersonalInfo columns
    pinfo_cols = [
        "full_name", "first_name", "last_name", "father_name", "gender", "date_of_birth",
        "cnic", "phone", "email", "address", "city", "postal_code", "country",
        "university", "degree", "department"
    ]

    action_taken = "CREATED"

    if canon_k in pinfo_cols:
        existing_info = user.personal_info
        if existing_info:
            update_data = {}
            if canon_k == "first_name" or canon_k == "last_name":
                # Only update name if full_name is present
                tokens = (existing_info.full_name or "").split()
                if canon_k == "first_name":
                    last = tokens[-1] if len(tokens) > 1 else ""
                    update_data["full_name"] = f"{val} {last}".strip()
                else:
                    first = tokens[0] if tokens else ""
                    update_data["full_name"] = f"{first} {val}".strip()
            else:
                update_data[canon_k] = val

            update_dto = PersonalInfoUpdate.model_validate(update_data)
            update_personal_info(db=db, user_id=user_id, info_in=update_dto)
            action_taken = "UPDATED_PERSONAL_INFO"
        else:
            init_data = {"full_name": user.full_name or val}
            if canon_k != "full_name":
                init_data[canon_k] = val
            create_dto = PersonalInfoCreate.model_validate(init_data)
            create_personal_info(db=db, user_id=user_id, info_in=create_dto)
            action_taken = "CREATED_PERSONAL_INFO"
    else:
        # 2. Save or update as dynamic CustomField
        category = request.category or "general"
        upsert_custom_field_by_key(
            db=db,
            user_id=user_id,
            field_key=canon_k,
            field_label=f_lbl,
            field_value=val,
            category=category
        )
        action_taken = "UPSERTED_CUSTOM_FIELD"

    # Refresh and return updated profile
    updated_profile = get_user_profile(db=db, user_id=user_id)

    return {
        "saved": True,
        "message": f"Successfully saved '{f_lbl}' to your personal memory vault.",
        "canonical_key": canon_k,
        "action_taken": action_taken,
        "profile_data": updated_profile
    }
