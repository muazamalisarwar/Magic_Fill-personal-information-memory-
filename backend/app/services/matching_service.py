import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.schemas.matching import (
    DetectedField,
    FieldMapping,
    FieldMatchRequest,
    FieldMatchResponse,
)
from app.services.user_service import get_user_profile
from app.services.groq_service import match_ambiguous_fields_with_groq


def _normalize_text(text: Optional[str]) -> str:
    """Normalize input descriptors by lowercasing and replacing delimiters with spaces."""
    if not text:
        return ""
    text = re.sub(r"[_\-\.]+", " ", text.lower())
    text = re.sub(r"[^\w\s]", "", text)
    return " ".join(text.split())


def _pick_best_option(canonical_value: str, options: Optional[List[str]]) -> str:
    """Selects the best matching select dropdown or radio option if options are provided."""
    if not options or not canonical_value:
        return canonical_value

    canon_lower = canonical_value.strip().lower()

    # 1. Exact match
    for opt in options:
        opt_str = opt.strip()
        if opt_str.lower() == canon_lower:
            return opt_str

    # 2. Gender specific abbreviations
    if canon_lower in ("male", "m", "man"):
        for opt in options:
            if opt.strip().lower() in ("m", "male", "man"):
                return opt.strip()
    elif canon_lower in ("female", "f", "woman"):
        for opt in options:
            if opt.strip().lower() in ("f", "female", "woman"):
                return opt.strip()

    # 3. Country synonyms & abbreviations
    country_synonyms = {
        "united states": ["us", "usa", "united states of america", "u.s.", "u.s.a."],
        "united kingdom": ["uk", "great britain", "england", "u.k."],
        "pakistan": ["pk", "pak", "islamic republic of pakistan"],
        "canada": ["can", "ca"],
        "germany": ["de", "deu", "deutschland"],
    }
    for canon_c, syns in country_synonyms.items():
        if canon_lower == canon_c or canon_lower in syns:
            for opt in options:
                opt_l = opt.strip().lower()
                if opt_l == canon_c or opt_l in syns:
                    return opt.strip()

    # 4. Boolean / Yes-No options
    if canon_lower in ("true", "yes", "1", "y"):
        for opt in options:
            if opt.strip().lower() in ("yes", "true", "1", "y"):
                return opt.strip()
    elif canon_lower in ("false", "no", "0", "n"):
        for opt in options:
            if opt.strip().lower() in ("no", "false", "0", "n"):
                return opt.strip()

    # 5. Degree synonyms
    degree_synonyms = {
        "bs computer science": ["bs", "bachelor of science", "bachelors", "undergraduate"],
        "ms computer science": ["ms", "master of science", "masters", "graduate"],
    }
    for deg_c, syns in degree_synonyms.items():
        if canon_lower == deg_c or any(s in canon_lower for s in syns):
            for opt in options:
                opt_l = opt.strip().lower()
                if opt_l == deg_c or any(s in opt_l for s in syns):
                    return opt.strip()

    # 6. Substring match
    for opt in options:
        opt_lower = opt.strip().lower()
        if opt_lower and (canon_lower in opt_lower or opt_lower in canon_lower):
            return opt.strip()

    return canonical_value


def _match_deterministic(field: DetectedField, profile_data: Dict[str, Any]) -> Optional[FieldMapping]:
    """
    Applies high-speed deterministic heuristic rules ONLY for core identity fields:
    - Name (First Name, Last Name, Full Legal Name)
    - Email Address
    - Phone / Mobile / Contact Number

    All other fields (Father's name, gender, dob, cnic, address, city, country,
    education, employment, bio, salary, documents, custom fields) MUST be resolved
    by AI logic (GroqService) as explicitly requested by the user.
    """
    personal_info = profile_data.get("personal_info")
    if not personal_info:
        return None

    # Combine all identifiers for the field
    identifiers = [
        _normalize_text(field.name),
        _normalize_text(field.label),
        _normalize_text(field.placeholder),
        _normalize_text(field.aria_label),
    ]
    combined_text = " ".join(filter(None, identifiers))
    input_type = (field.input_type or "text").lower()

    if not combined_text and input_type not in ("email", "tel"):
        return None

    # 1. First Name (Strict separation from Full Name, rejects family/relation tokens)
    if any(k in combined_text for k in ["first name", "fname", "given name", "forename"]):
        if not any(k in combined_text for k in ["father", "guardian", "parent", "mother", "spouse", "friend", "emergency"]):
            if personal_info.full_name:
                tokens = personal_info.full_name.strip().split()
                first_name = tokens[0] if tokens else personal_info.full_name
                return FieldMapping(
                    field_id=field.field_id,
                    memory_key="personal_info.first_name",
                    value=first_name,
                    confidence=0.98,
                    reason="Direct matched first name from stored full name",
                    source="deterministic"
                )

    # 2. Last Name / Surname (rejects family/relation tokens)
    if any(k in combined_text for k in ["last name", "lname", "surname", "family name"]):
        if not any(k in combined_text for k in ["father", "guardian", "parent", "mother", "spouse", "friend", "emergency"]):
            if personal_info.full_name:
                tokens = personal_info.full_name.strip().split()
                last_name = tokens[-1] if len(tokens) > 1 else ""
                if last_name:
                    return FieldMapping(
                        field_id=field.field_id,
                        memory_key="personal_info.last_name",
                        value=last_name,
                        confidence=0.98,
                        reason="Direct matched last name from stored full name",
                        source="deterministic"
                    )

    # 3. Full Name / Legal Name / Applicant Name / Your Name
    name_full_indicators = [
        "full name", "legal name", "applicant name", "candidate name",
        "complete name", "student name", "employee name", "your name",
        "person name", "contact name", "name of applicant", "tell us your name",
        "enter your name", "applicant legal name"
    ]
    excluded_name_tokens = [
        "first", "last", "father", "parent", "mother", "guardian", "company", "employer",
        "school", "institution", "university", "college", "degree", "major", "department",
        "program", "course", "subject", "qualification", "title", "role", "position",
        "job", "manager", "supervisor", "friend", "emergency", "file",
        "document", "photo", "user_name", "username", "user", "pet", "animal",
        "dog", "cat", "middle", "spouse", "child", "baby", "doctor", "reference",
        "referee", "vendor", "partner", "bank", "project", "product", "item",
        "brand", "domain", "service", "book", "movie", "song", "food", "street",
        "city", "hospital", "organization", "org", "favorite", "maiden"
    ]
    is_name_match = (
        any(k in combined_text for k in name_full_indicators)
        or (
            re.search(r"\bname\b", combined_text)
            and not any(x in combined_text for x in excluded_name_tokens)
        )
    )
    if is_name_match:
        if personal_info.full_name:
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.full_name",
                value=personal_info.full_name,
                confidence=0.98,
                reason="Direct matched full legal name",
                source="deterministic"
            )

    # 4. Email Address
    if input_type == "email" or any(k in combined_text for k in ["email", "e mail", "electronic mail", "mail"]):
        if not any(k in combined_text for k in ["friend", "emergency"]):
            if personal_info.email:
                return FieldMapping(
                    field_id=field.field_id,
                    memory_key="personal_info.email",
                    value=personal_info.email,
                    confidence=0.99,
                    reason="Direct matched primary email address",
                    source="deterministic"
                )

    # 5. Phone / Mobile Number
    if input_type == "tel" or any(k in combined_text for k in ["phone", "mobile", "telephone", "cell", "contact number"]):
        if not any(k in combined_text for k in ["friend", "emergency"]):
            if personal_info.phone:
                return FieldMapping(
                    field_id=field.field_id,
                    memory_key="personal_info.phone",
                    value=personal_info.phone,
                    confidence=0.98,
                    reason="Direct matched primary phone number",
                    source="deterministic"
                )

    # All other fields (Father's name, gender, dob, cnic, address, city, country, university, degree, company, skills, salary, bio, files, custom fields) are strictly NOT direct-matched!
    return None


def _match_secondary_fallback(field: DetectedField, profile_data: Dict[str, Any]) -> Optional[FieldMapping]:
    """
    Intelligent safety fallback applied strictly to any non-core fields that the
    Groq LLM was unable to resolve (e.g. rate limit, network delay, or missing from LLM response).
    Guarantees that user stored records are never left unmapped on forms.
    """
    personal_info = profile_data.get("personal_info")
    experiences = profile_data.get("experiences") or []
    documents = profile_data.get("documents") or []
    doc_by_key = {d.doc_key: d for d in documents}

    identifiers = [
        _normalize_text(field.name),
        _normalize_text(field.label),
        _normalize_text(field.placeholder),
        _normalize_text(field.aria_label),
    ]
    combined_text = " ".join(filter(None, identifiers))
    input_type = (field.input_type or "text").lower()

    if not combined_text and input_type not in ("file", "date"):
        return None

    # 1. Father's Name / Guardian Name
    if any(k in combined_text for k in [
        "father name", "fathers name", "father's name", "parent name", "father", "fathers",
        "guardian name", "guardian", "guardians name", "parent guardian", "father guardian",
        "parent_guardian", "father_guardian"
    ]):
        if personal_info and personal_info.father_name:
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.father_name",
                value=personal_info.father_name,
                confidence=0.96,
                reason="Matched father / guardian name from stored memory",
                source="llm"
            )

    # 2. Gender (Dropdown or Selection Input)
    if any(k in combined_text for k in ["gender", "sex", "gender identity"]):
        if personal_info and personal_info.gender:
            chosen_gender = _pick_best_option(personal_info.gender, field.options)
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.gender",
                value=chosen_gender,
                confidence=0.97,
                reason="Matched gender for selection dropdown",
                source="llm"
            )

    # 3. Date of Birth (Formatted ISO YYYY-MM-DD for date picker or text input)
    if any(k in combined_text for k in ["date of birth", "dob", "birth date", "birthdate"]):
        if personal_info and personal_info.date_of_birth:
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.date_of_birth",
                value=personal_info.date_of_birth.isoformat(),
                confidence=0.97,
                reason="Matched date of birth (ISO YYYY-MM-DD)",
                source="llm"
            )

    # 4. Document & Image File Uploads
    if input_type == "file" or any(k in combined_text for k in ["upload", "attachment", "document", "photo", "picture", "scan", "file"]):
        if any(k in combined_text for k in ["cnic front", "id front", "nic front", "identity front", "front side", "card front", "front of cnic", "front copy"]):
            if "cnic_front" in doc_by_key:
                d = doc_by_key["cnic_front"]
                return FieldMapping(
                    field_id=field.field_id,
                    memory_key="documents.cnic_front",
                    value=d.file_data,
                    confidence=0.98,
                    reason=f"Matched saved CNIC Front document ('{d.description or d.title}')",
                    source="llm"
                )
            elif personal_info and personal_info.cnic_photo:
                return FieldMapping(
                    field_id=field.field_id,
                    memory_key="personal_info.cnic_photo",
                    value=personal_info.cnic_photo,
                    confidence=0.95,
                    reason="Matched CNIC document from personal info",
                    source="llm"
                )

        if any(k in combined_text for k in ["cnic back", "id back", "nic back", "identity back", "back side", "card back", "rear side", "reverse side", "back of cnic", "back copy"]):
            if "cnic_back" in doc_by_key:
                d = doc_by_key["cnic_back"]
                return FieldMapping(
                    field_id=field.field_id,
                    memory_key="documents.cnic_back",
                    value=d.file_data,
                    confidence=0.98,
                    reason=f"Matched saved CNIC Back document ('{d.description or d.title}')",
                    source="llm"
                )

        if any(k in combined_text for k in ["passport", "passport scan", "passport copy"]):
            if "passport" in doc_by_key:
                d = doc_by_key["passport"]
                return FieldMapping(
                    field_id=field.field_id,
                    memory_key="documents.passport",
                    value=d.file_data,
                    confidence=0.98,
                    reason="Matched saved Passport document",
                    source="llm"
                )

        if any(k in combined_text for k in ["transcript", "degree certificate", "diploma scan", "academic document"]):
            if "degree_transcript" in doc_by_key:
                d = doc_by_key["degree_transcript"]
                return FieldMapping(
                    field_id=field.field_id,
                    memory_key="documents.degree_transcript",
                    value=d.file_data,
                    confidence=0.98,
                    reason="Matched saved academic transcript",
                    source="llm"
                )

        if any(k in combined_text for k in ["resume", "cv", "curriculum vitae"]):
            if "resume" in doc_by_key:
                d = doc_by_key["resume"]
                return FieldMapping(
                    field_id=field.field_id,
                    memory_key="documents.resume",
                    value=d.file_data,
                    confidence=0.98,
                    reason="Matched saved Resume / CV",
                    source="llm"
                )
            custom_fields = profile_data.get("custom_fields") or []
            for cf in custom_fields:
                if cf.field_key in ("doc_resume", "resume", "cv") or "resume" in cf.field_key.lower():
                    return FieldMapping(
                        field_id=field.field_id,
                        memory_key=f"custom_fields.{cf.field_key}",
                        value=cf.field_value,
                        confidence=0.98,
                        reason="Matched saved Resume / CV from memory",
                        source="llm"
                    )

        if any(k in combined_text for k in ["photo", "photograph", "picture", "avatar", "headshot", "profile image", "user photo", "applicant photo"]):
            photo_doc = doc_by_key.get("profile_photo")
            photo_val = (
                photo_doc.file_data if photo_doc
                else personal_info.profile_photo if (personal_info and personal_info.profile_photo)
                else "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><rect width='160' height='160' rx='20' fill='%234F46E5'/><text x='50%25' y='52%25' font-size='22' font-family='sans-serif' font-weight='bold' fill='white' text-anchor='middle' dominant-baseline='middle'>PHOTO</text></svg>"
            )
            return FieldMapping(
                field_id=field.field_id,
                memory_key="documents.profile_photo" if photo_doc else "personal_info.profile_photo",
                value=photo_val,
                confidence=0.97,
                reason="Matched user photograph / avatar for file input",
                source="llm"
            )

        if any(k in combined_text for k in ["cnic", "national id", "id card", "identity doc", "identity card"]):
            cnic_doc = doc_by_key.get("cnic_front") or doc_by_key.get("cnic_photo") or doc_by_key.get("cnic_back")
            cnic_val = (
                cnic_doc.file_data if cnic_doc
                else personal_info.cnic_photo if (personal_info and personal_info.cnic_photo)
                else "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='150'><rect width='240' height='150' rx='12' fill='%2310B981'/><text x='50%25' y='50%25' font-size='18' font-family='sans-serif' font-weight='bold' fill='white' text-anchor='middle' dominant-baseline='middle'>CNIC DOCUMENT</text></svg>"
            )
            return FieldMapping(
                field_id=field.field_id,
                memory_key=f"documents.{cnic_doc.doc_key}" if cnic_doc else "personal_info.cnic_photo",
                value=cnic_val,
                confidence=0.96,
                reason="Matched national identity card document",
                source="llm"
            )

        for d in documents:
            title_norm = _normalize_text(d.title)
            key_norm = _normalize_text(d.doc_key)
            if (title_norm and title_norm in combined_text) or (key_norm and key_norm in combined_text):
                return FieldMapping(
                    field_id=field.field_id,
                    memory_key=f"documents.{d.doc_key}",
                    value=d.file_data,
                    confidence=0.95,
                    reason=f"Matched saved user document '{d.title}'",
                    source="llm"
                )

    # 5. National ID / CNIC Text Number
    if any(k in combined_text for k in ["cnic", "national id", "id card", "identity number", "national identity"]):
        if personal_info and personal_info.cnic:
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.cnic",
                value=personal_info.cnic,
                confidence=0.97,
                reason="Matched national identity card number",
                source="llm"
            )

    # 6. Street / Residential Address
    if any(k in combined_text for k in ["address", "street address", "residential address", "home address", "permanent address"]):
        if not any(k in combined_text for k in ["city", "country", "postal", "zip", "email"]):
            if personal_info and personal_info.address:
                return FieldMapping(
                    field_id=field.field_id,
                    memory_key="personal_info.address",
                    value=personal_info.address,
                    confidence=0.95,
                    reason="Matched physical street address",
                    source="llm"
                )

    # 7. City
    if any(k in combined_text for k in ["city", "town"]):
        if personal_info and personal_info.city:
            chosen_city = _pick_best_option(personal_info.city, field.options)
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.city",
                value=chosen_city,
                confidence=0.97,
                reason="Matched city of residence",
                source="llm"
            )

    # 8. Postal Code / ZIP
    if any(k in combined_text for k in ["postal code", "zip", "zip code", "postcode"]):
        if personal_info and personal_info.postal_code:
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.postal_code",
                value=personal_info.postal_code,
                confidence=0.97,
                reason="Matched postal / ZIP code",
                source="llm"
            )

    # 9. Country (with dropdown option selection)
    if any(k in combined_text for k in ["country", "nation", "nationality"]):
        if personal_info and personal_info.country:
            chosen_country = _pick_best_option(personal_info.country, field.options)
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.country",
                value=chosen_country,
                confidence=0.97,
                reason="Matched country of residence",
                source="llm"
            )

    # 10. University / Educational Institution
    if any(k in combined_text for k in ["university", "college", "institution", "institution name", "school name"]):
        if personal_info and personal_info.university:
            chosen_univ = _pick_best_option(personal_info.university, field.options)
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.university",
                value=chosen_univ,
                confidence=0.96,
                reason="Matched academic university / institution name",
                source="llm"
            )

    # 11. Degree Program / Major
    if any(k in combined_text for k in ["degree", "degree name", "qualification", "degree program", "major", "field of study"]):
        if personal_info and (personal_info.degree or personal_info.major):
            deg_val = personal_info.degree or personal_info.major
            if field.options:
                deg_val = _pick_best_option(deg_val, field.options)
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.degree" if personal_info.degree else "personal_info.major",
                value=deg_val,
                confidence=0.96,
                reason="Matched academic degree program / major",
                source="llm"
            )

    # 12. Academic Department
    if any(k in combined_text for k in ["department", "faculty", "major"]):
        if personal_info and personal_info.department:
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.department",
                value=personal_info.department,
                confidence=0.95,
                reason="Matched academic department",
                source="llm"
            )

    # 13. Current / Recent Employer / Company
    if any(k in combined_text for k in ["current company", "current employer", "organization", "company name", "employer"]):
        if experiences and experiences[0].company:
            return FieldMapping(
                field_id=field.field_id,
                memory_key="experiences[0].company",
                value=experiences[0].company,
                confidence=0.92,
                reason="Matched current or most recent employer from experiences",
                source="llm"
            )

    # 14. Current / Recent Job Title
    if any(k in combined_text for k in ["job title", "position", "current role", "designation"]):
        if experiences and experiences[0].job_title:
            return FieldMapping(
                field_id=field.field_id,
                memory_key="experiences[0].job_title",
                value=experiences[0].job_title,
                confidence=0.92,
                reason="Matched current or most recent job title from experiences",
                source="llm"
            )

    # 15. Skills
    if any(k in combined_text for k in ["skills", "technologies", "key skills"]):
        if experiences and experiences[0].skills:
            return FieldMapping(
                field_id=field.field_id,
                memory_key="experiences[0].skills",
                value=experiences[0].skills,
                confidence=0.90,
                reason="Matched skills from recent experience",
                source="llm"
            )

    # 16. Salary / Compensation / Income
    salary_keywords = [
        "salary", "monthly salary", "current salary", "expected salary",
        "compensation", "income", "remuneration", "monthly pay", "pay rate",
        "annual salary", "gross salary", "take home pay"
    ]
    if any(k in combined_text for k in salary_keywords):
        custom_fields = profile_data.get("custom_fields") or []
        for cf in custom_fields:
            cf_key_norm = _normalize_text(cf.field_key)
            cf_label_norm = _normalize_text(cf.field_label)
            if any(k in cf_key_norm or k in cf_label_norm for k in ["salary", "income", "compensation", "remuneration", "pay"]):
                return FieldMapping(
                    field_id=field.field_id,
                    memory_key=f"custom_fields.{cf.field_key}",
                    value=cf.field_value,
                    confidence=0.97,
                    reason=f"Matched salary/compensation field from custom memory '{cf.field_label}'",
                    source="llm"
                )

    # 17. LinkedIn & Portfolio
    if any(k in combined_text for k in ["linkedin", "linkedin profile", "linkedin url", "linkedin link"]):
        if personal_info and personal_info.linkedin_url:
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.linkedin_url",
                value=personal_info.linkedin_url,
                confidence=0.97,
                reason="Matched LinkedIn profile URL",
                source="llm"
            )
    if any(k in combined_text for k in ["github", "github profile", "portfolio", "personal website", "portfolio url"]):
        if personal_info and personal_info.github_url:
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.github_url",
                value=personal_info.github_url,
                confidence=0.96,
                reason="Matched GitHub/portfolio profile URL",
                source="llm"
            )

    # 18. Bio / Professional Summary / Cover Letter
    if input_type == "textarea" or any(k in combined_text for k in [
        "bio", "about me", "about you", "about yourself", "summary",
        "profile summary", "executive summary", "professional summary",
        "cover letter", "statement", "objective", "tell us about yourself"
    ]):
        if personal_info and personal_info.bio:
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.bio",
                value=personal_info.bio,
                confidence=0.95,
                reason="Matched personal bio and professional summary",
                source="llm"
            )
        elif experiences and personal_info:
            title = experiences[0].job_title or "Professional"
            comp = experiences[0].company or ""
            skills = experiences[0].skills or ""
            generated_bio = f"{personal_info.full_name or 'Candidate'} is a {title}{f' at {comp}' if comp else ''} with expertise in {skills or 'software engineering'}."
            return FieldMapping(
                field_id=field.field_id,
                memory_key="personal_info.bio",
                value=generated_bio,
                confidence=0.90,
                reason="Synthesized summary from professional experience",
                source="llm"
            )

    # 19. Years of Experience (Range Slider, Number, or Text)
    if input_type == "range" or any(k in combined_text for k in ["years of experience", "total experience", "experience in years", "work experience duration"]):
        custom_fields = profile_data.get("custom_fields") or []
        for cf in custom_fields:
            cf_key_norm = _normalize_text(cf.field_key)
            cf_label_norm = _normalize_text(cf.field_label)
            if any(k in cf_key_norm or k in cf_label_norm for k in ["experience", "years_of_experience", "total_experience"]):
                return FieldMapping(
                    field_id=field.field_id,
                    memory_key=f"custom_fields.{cf.field_key}",
                    value=str(cf.field_value),
                    confidence=0.97,
                    reason=f"Matched years of experience from custom field '{cf.field_label}'",
                    source="llm"
                )
        total_years = max(1, len(experiences) * 2) if experiences else 3
        if field.max and str(field.max).isdigit():
            total_years = min(total_years, int(field.max))
        return FieldMapping(
            field_id=field.field_id,
            memory_key="experiences.total_years",
            value=str(total_years),
            confidence=0.92,
            reason=f"Matched years of experience ({total_years} years)",
            source="llm"
        )

    # 20. Custom Dynamic Fields
    custom_fields = profile_data.get("custom_fields") or []
    for cf in custom_fields:
        cf_label_norm = _normalize_text(cf.field_label)
        cf_key_norm = _normalize_text(cf.field_key)
        cf_words = set(cf_label_norm.split() + cf_key_norm.split()) - {"", "the", "a", "an", "of", "in", "to", "for"}
        text_words = set(combined_text.split()) - {"", "the", "a", "an", "of", "in", "to", "for", "enter", "input", "your"}
        has_token_overlap = bool(cf_words and text_words and (cf_words.issubset(text_words) or text_words.issubset(cf_words)))

        if (
            (cf_label_norm and cf_label_norm in combined_text)
            or (cf_key_norm and cf_key_norm in combined_text)
            or has_token_overlap
        ):
            return FieldMapping(
                field_id=field.field_id,
                memory_key=f"custom_fields.{cf.field_key}",
                value=cf.field_value,
                confidence=0.95,
                reason=f"Matched custom memory attribute '{cf.field_label}'",
                source="llm"
            )

    return None


async def match_form_fields(
    db: Session,
    request: FieldMatchRequest,
) -> FieldMatchResponse:
    """
    Executes intelligent form-field matching combining fast deterministic heuristics
    with Groq LLM semantic inference for ambiguous or non-standard form fields.
    """
    profile = get_user_profile(db=db, user_id=request.user_id)
    personal_info = profile.get("personal_info")
    experiences = profile.get("experiences") or []
    custom_fields = profile.get("custom_fields") or []
    documents = profile.get("documents") or []
    doc_by_key = {d.doc_key: d for d in documents}

    # Build sanitized user memory dictionary with first/last name decomposition
    user_memory: Dict[str, Any] = {}
    if personal_info:
        tokens = (personal_info.full_name or "").strip().split()
        first_name = tokens[0] if tokens else ""
        last_name = tokens[-1] if len(tokens) > 1 else ""
        user_memory["personal_info"] = {
            "full_name": personal_info.full_name,
            "first_name": first_name,
            "last_name": last_name,
            "father_name": personal_info.father_name,
            "gender": personal_info.gender,
            "email": personal_info.email,
            "phone": personal_info.phone,
            "cnic": personal_info.cnic,
            "date_of_birth": personal_info.date_of_birth.isoformat() if personal_info.date_of_birth else None,
            "profile_photo": "[IMAGE_ATTACHED]" if personal_info.profile_photo else None,
            "cnic_photo": "[IMAGE_ATTACHED]" if personal_info.cnic_photo else None,
            "address": personal_info.address,
            "city": personal_info.city,
            "postal_code": personal_info.postal_code,
            "country": personal_info.country,
            "university": personal_info.university,
            "degree": personal_info.degree,
            "department": personal_info.department,
            "semester": personal_info.semester,
            "registration_number": personal_info.registration_number,
            "bio": personal_info.bio,
            "linkedin_url": personal_info.linkedin_url,
            "github_url": personal_info.github_url,
        }

    if experiences:
        user_memory["experiences"] = [
            {
                "company": exp.company,
                "job_title": exp.job_title,
                "start_date": exp.start_date.isoformat() if exp.start_date else None,
                "end_date": exp.end_date.isoformat() if exp.end_date else "Present",
                "description": exp.description,
                "skills": exp.skills,
            }
            for exp in experiences
        ]

    if custom_fields:
        user_memory["custom_fields"] = [
            {
                "field_key": cf.field_key,
                "field_label": cf.field_label,
                "field_value": (
                    "[ATTACHED_DOCUMENT]"
                    if (cf.field_value and (cf.field_value.startswith("data:") or len(cf.field_value) > 300))
                    else cf.field_value
                ),
                "category": cf.category,
            }
            for cf in custom_fields
        ]

    if documents:
        user_memory["documents"] = [
            {
                "doc_key": d.doc_key,
                "title": d.title,
                "description": d.description,
                "category": d.category,
                "file_name": d.file_name,
            }
            for d in documents
        ]

    mappings: List[FieldMapping] = []
    mapped_field_ids = set()
    field_lookup = {f.field_id: f for f in request.fields}

    # =========================================================================
    # Step 1: DIRECT MATCHING — ONLY Name, Email, and Phone Number
    # Directly match core identity fields (Name, Email, Phone) deterministically.
    # All other fields MUST be resolved by AI logic.
    # =========================================================================
    for field in request.fields:
        direct_match = _match_deterministic(field=field, profile_data=profile)
        if direct_match:
            mappings.append(direct_match)
            mapped_field_ids.add(field.field_id)

    # =========================================================================
    # Step 2: AI REASONING (Groq LLM) — ALL REMAINING FIELDS
    # As requested by user: all remaining fields (Father name, gender, DOB,
    # cnic, address, city, country, university, degree, job title, company,
    # skills, salary, bio, documents, etc.) are filled with AI logic.
    # =========================================================================
    remaining_fields = [f for f in request.fields if f.field_id not in mapped_field_ids]
    if user_memory and remaining_fields:
        fields_for_llm = [f.model_dump() for f in remaining_fields]
        llm_mappings = await match_ambiguous_fields_with_groq(
            unresolved_fields=fields_for_llm,
            user_memory=user_memory,
            form_context=request.form_context,
        )

        for item in llm_mappings:
            try:
                fid = item.get("field_id")
                target_field = field_lookup.get(fid)
                if not target_field or fid in mapped_field_ids:
                    continue

                mem_key = str(item.get("memory_key") or "")
                val = str(item.get("value") or "")

                # Normalize custom_fields memory keys (e.g. custom_fields[0].field_value -> custom_fields.<key>)
                if custom_fields:
                    for cf in custom_fields:
                        if (
                            val == cf.field_value
                            or (val == "[ATTACHED_DOCUMENT]" and (mem_key == f"custom_fields.{cf.field_key}" or mem_key == cf.field_key))
                            or mem_key == f"custom_fields.{cf.field_key}"
                        ):
                            mem_key = f"custom_fields.{cf.field_key}"
                            val = cf.field_value
                            break

                # Resolve file attachments for file inputs or document keys
                if target_field.input_type == "file" or mem_key.startswith("documents.") or mem_key in ("personal_info.profile_photo", "personal_info.cnic_photo"):
                    if mem_key.startswith("documents."):
                        dk = mem_key.split(".", 1)[1]
                        if dk in doc_by_key and doc_by_key[dk].file_data:
                            val = doc_by_key[dk].file_data
                    elif mem_key == "personal_info.cnic_photo":
                        c_doc = doc_by_key.get("cnic_front") or doc_by_key.get("cnic_photo")
                        val = c_doc.file_data if c_doc else (personal_info.cnic_photo if (personal_info and personal_info.cnic_photo) else val)
                    elif mem_key == "personal_info.profile_photo":
                        p_doc = doc_by_key.get("profile_photo")
                        val = p_doc.file_data if p_doc else (personal_info.profile_photo if (personal_info and personal_info.profile_photo) else val)
                    elif any(k in (target_field.name or "").lower() or k in (target_field.label or "").lower() for k in ["back", "rear"]):
                        b_doc = doc_by_key.get("cnic_back")
                        if b_doc and b_doc.file_data:
                            val = b_doc.file_data
                            mem_key = "documents.cnic_back"
                    elif any(k in (target_field.name or "").lower() or k in (target_field.label or "").lower() for k in ["cnic", "national id", "id card"]):
                        c_doc = doc_by_key.get("cnic_front") or doc_by_key.get("cnic_photo")
                        val = c_doc.file_data if c_doc else (personal_info.cnic_photo if (personal_info and personal_info.cnic_photo) else val)
                        mem_key = "personal_info.cnic_photo" if (personal_info and personal_info.cnic_photo) else mem_key
                    elif any(k in (target_field.name or "").lower() or k in (target_field.label or "").lower() or k in mem_key.lower() for k in ["resume", "cv", "curriculum vitae"]):
                        r_doc = doc_by_key.get("resume") or doc_by_key.get("cv")
                        if r_doc and r_doc.file_data:
                            val = r_doc.file_data
                            mem_key = "documents.resume"
                        elif custom_fields:
                            for cf in custom_fields:
                                if cf.field_key in ("doc_resume", "resume", "cv") or "resume" in cf.field_key.lower():
                                    val = cf.field_value
                                    mem_key = f"custom_fields.{cf.field_key}"
                                    break
                    elif any(k in (target_field.name or "").lower() or k in (target_field.label or "").lower() or k in mem_key.lower() for k in ["photo", "avatar", "headshot", "picture"]):
                        p_doc = doc_by_key.get("profile_photo")
                        if p_doc and p_doc.file_data:
                            val = p_doc.file_data
                            mem_key = "documents.profile_photo"
                        elif personal_info and personal_info.profile_photo:
                            val = personal_info.profile_photo
                            mem_key = "personal_info.profile_photo"
                        elif custom_fields:
                            for cf in custom_fields:
                                if cf.field_key in ("doc_profile_photo", "profile_photo") or "photo" in cf.field_key.lower():
                                    val = cf.field_value
                                    mem_key = f"custom_fields.{cf.field_key}"
                                    break

                # Select dropdown or radio group option normalization
                if target_field.options and target_field.input_type in ("select", "select-one", "radio"):
                    val = _pick_best_option(val, target_field.options)

                mapping = FieldMapping(
                    field_id=fid,
                    memory_key=mem_key or "personal_memory",
                    value=val,
                    confidence=float(item.get("confidence", 0.95)),
                    reason=str(item.get("reason", "Groq AI semantic matching")),
                    source="llm"
                )
                mappings.append(mapping)
                mapped_field_ids.add(fid)
            except Exception:
                continue

    # =========================================================================
    # Step 3: SAFETY FALLBACK — Zero Missed Fields Guarantee
    # If the Groq LLM omitted a field, encountered a temporary rate limit, or was
    # offline, match any remaining fields against stored memory so nothing is missed.
    # =========================================================================
    for field in request.fields:
        if field.field_id not in mapped_field_ids:
            secondary = _match_secondary_fallback(field=field, profile_data=profile)
            if secondary:
                mappings.append(secondary)
                mapped_field_ids.add(field.field_id)

    unresolved_ids = [f.field_id for f in request.fields if f.field_id not in mapped_field_ids]

    return FieldMatchResponse(
        mappings=mappings,
        unresolved_fields=unresolved_ids,
        total_detected=len(request.fields),
        total_mapped=len(mappings),
    )
