import io
import json
import logging
import re
import datetime
import zipfile
import xml.etree.ElementTree as ET
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


HEADER_SECTION_PATTERN = re.compile(
    r'^(?:[#*_\-\s]*)(PROFESSIONAL\s+SUMMARY|SUMMARY|OBJECTIVE|PROFILE|EXECUTIVE\s+SUMMARY|'
    r'KEY\s+SKILLS|TECHNICAL\s+SKILLS|CORE\s+SKILLS|CORE\s+COMPETENCIES|SKILLS|TECHNOLOGIES|PROGRAMMING\s+SKILLS|'
    r'LEARNING\s*&?\s*DEVELOPMENT|COURSES|TRAINING|PROFESSIONAL\s+DEVELOPMENT|'
    r'WORK\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EMPLOYMENT\s+HISTORY|EXPERIENCE|CAREER\s+HISTORY|WORK\s+HISTORY|'
    r'RELEVANT\s+PROJECTS(?:\s*\(.*?\))?|KEY\s+PROJECTS|PROJECTS|ACADEMIC\s+PROJECTS|PERSONAL\s+PROJECTS|'
    r'ACADEMIC\s+BACKGROUND|EDUCATION|ACADEMIC\s+QUALIFICATIONS|QUALIFICATIONS|'
    r'CERTIFICATIONS|CERTIFICATES|LICENSES|LICENSES\s*&?\s*CERTIFICATIONS|'
    r'HONORS|AWARDS|LANGUAGES|PUBLICATIONS|VOLUNTEERING|VOLUNTEER\s+EXPERIENCE)(?:[\s:*_\-]*)$',
    re.IGNORECASE | re.MULTILINE
)


def split_into_semantic_chunks(text: str) -> List[Dict[str, Any]]:
    """
    Splits resume or document text into meaningful, labeled semantic chunks
    based on standard document section boundaries or logical paragraph clusters.
    """
    clean = text.strip()
    if not clean:
        return []

    matches = list(HEADER_SECTION_PATTERN.finditer(clean))
    chunks: List[Dict[str, Any]] = []

    if matches:
        last_pos = 0
        last_header = "HEADER & CONTACT"
        for m in matches:
            start, end = m.span()
            content = clean[last_pos:start].strip()
            if content:
                chunks.append({
                    "chunk_id": len(chunks) + 1,
                    "title": last_header,
                    "content": content,
                    "char_count": len(content)
                })
            last_header = m.group(1).strip().upper()
            last_pos = end

        final_content = clean[last_pos:].strip()
        if final_content:
            chunks.append({
                "chunk_id": len(chunks) + 1,
                "title": last_header,
                "content": final_content,
                "char_count": len(final_content)
            })
    else:
        # Fallback to paragraph-based chunking with boundary awareness
        paragraphs = [p.strip() for p in clean.split("\n\n") if p.strip()]
        current_block: List[str] = []
        current_len = 0
        for p in paragraphs:
            current_block.append(p)
            current_len += len(p)
            if current_len >= 1400:
                block_content = "\n\n".join(current_block).strip()
                chunks.append({
                    "chunk_id": len(chunks) + 1,
                    "title": f"Section {len(chunks) + 1}",
                    "content": block_content,
                    "char_count": len(block_content)
                })
                current_block = []
                current_len = 0
        if current_block:
            block_content = "\n\n".join(current_block).strip()
            chunks.append({
                "chunk_id": len(chunks) + 1,
                "title": f"Section {len(chunks) + 1}",
                "content": block_content,
                "char_count": len(block_content)
            })

    return chunks or [{
        "chunk_id": 1,
        "title": "Document Content",
        "content": clean,
        "char_count": len(clean)
    }]


def normalize_date_for_storage(val: Any, is_end_date: bool = False) -> Optional[datetime.date]:
    """
    Robustly parses and normalizes diverse date representations found in CVs/PDFs/DOCX.
    Handles:
    - '2022' -> 2022-01-01 (or 2022-12-31 for end_date)
    - '2022-05' -> 2022-05-01
    - 'May 2022', 'May, 2022', 'January 2024' -> 2022-05-01
    - '05/2022' -> 2022-05-01
    - '2022-05-14' -> 2022-05-14
    - '6 months', '1 year' -> estimated start date
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

    # Handle relative duration strings (e.g. '6 months', '1 year')
    m_dur = re.search(r"(\d+)\s*(month|year)", val_str, re.IGNORECASE)
    if m_dur:
        amount = int(m_dur.group(1))
        unit = m_dur.group(2).lower()
        days = amount * 30 if "month" in unit else amount * 365
        approx_start = datetime.date.today() - datetime.timedelta(days=days)
        return approx_start

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
    Extracts high-fidelity plain text from uploaded file bytes (PDF, Word DOCX/DOC, TXT, MD).
    - For Word (.docx / .doc / zip stream): extracts all paragraphs, section headers/footers,
      and tables cell-by-cell with structural markdown formatting.
    - For PDFs: utilizes dual-pass layout-aware parsing without OCR to preserve column structures,
      sidebars, tables, and form fields from modern resumes.
    - For plaintext / markdown: parses UTF-8 with latin-1 fallback.
    """
    filename_lower = filename.lower()
    is_zip = content_bytes[:4] == b"PK\x03\x04"
    is_docx = filename_lower.endswith((".docx", ".doc")) or (is_zip and not filename_lower.endswith(".pdf"))

    if is_docx:
        # Extract Microsoft Word document
        extracted_lines: List[str] = []
        try:
            import docx
            doc = docx.Document(io.BytesIO(content_bytes))
            # 1. Section headers & footers
            for sec in doc.sections:
                try:
                    for p in sec.header.paragraphs:
                        if p.text.strip():
                            extracted_lines.append(p.text.strip())
                except Exception:
                    pass

            # 2. Body paragraphs
            for p in doc.paragraphs:
                txt = p.text.strip()
                if txt:
                    extracted_lines.append(txt)

            # 3. Tables (formatted row by row)
            for t in doc.tables:
                for r in t.rows:
                    row_cells = [c.text.strip() for c in r.cells if c.text.strip()]
                    if row_cells:
                        extracted_lines.append(" | ".join(row_cells))

            # 4. Section footers
            for sec in doc.sections:
                try:
                    for p in sec.footer.paragraphs:
                        if p.text.strip():
                            extracted_lines.append(p.text.strip())
                except Exception:
                    pass

            full_text = "\n".join(extracted_lines).strip()
            if full_text:
                return full_text
        except Exception as exc:
            logger.warning("python-docx extraction failed for %s, trying XML parser: %s", filename, exc)

        # Fallback: Extract directly from docx zip archive XML
        try:
            with zipfile.ZipFile(io.BytesIO(content_bytes)) as z:
                xml_content = z.read("word/document.xml")
                tree = ET.fromstring(xml_content)
                xml_texts = [elem.text.strip() for elem in tree.iter() if elem.text and elem.text.strip()]
                if xml_texts:
                    return "\n".join(xml_texts).strip()
        except Exception as xml_exc:
            logger.warning("Direct docx XML extraction failed: %s", xml_exc)

        # Legacy binary .doc fallback (extract printable text strings)
        printable_runs = re.findall(rb"[\x20-\x7E\t\r\n]{4,}", content_bytes)
        if printable_runs:
            decoded_runs = [r.decode("latin-1", errors="ignore").strip() for r in printable_runs if r.strip()]
            return "\n".join(decoded_runs).strip()

        return ""

    elif filename_lower.endswith(".pdf") or content_bytes[:4] == b"%PDF":
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
            except Exception:
                layout_txt = ""

            # Pass 2: Try standard plain extraction
            try:
                plain_txt = page.extract_text(extraction_mode="plain", orientations=(0, 90, 180, 270))
            except Exception:
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


def merge_extracted_records(primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Intelligently merges two extracted profile record sets:
    - Merges personal_info non-null keys without overwriting existing primary data.
    - Appends experiences with de-duplication on (company, job_title).
    - Appends custom_fields with de-duplication on field_key.
    """
    merged_pi = dict(primary.get("personal_info") or {}) if primary.get("personal_info") else {}
    sec_pi = dict(secondary.get("personal_info") or {}) if secondary.get("personal_info") else {}
    for k, v in sec_pi.items():
        if v and not merged_pi.get(k):
            merged_pi[k] = v

    if not any(merged_pi.values()):
        merged_pi = None

    merged_exps = list(primary.get("experiences") or [])
    existing_exp_keys = set()
    for e in merged_exps:
        if isinstance(e, dict):
            c = re.sub(r"[^a-z0-9]+", "", (e.get("company") or "").lower())
            j = re.sub(r"[^a-z0-9]+", "", (e.get("job_title") or "").lower())
            if c and j:
                existing_exp_keys.add((c, j))

    for e in (secondary.get("experiences") or []):
        if isinstance(e, dict):
            c = re.sub(r"[^a-z0-9]+", "", (e.get("company") or "").lower())
            j = re.sub(r"[^a-z0-9]+", "", (e.get("job_title") or "").lower())
            is_dup = False
            for ec, ej in existing_exp_keys:
                if (c == ec or c in ec or ec in c) and (j == ej or j in ej or ej in j):
                    is_dup = True
                    break
            if not is_dup and c and j:
                merged_exps.append(e)
                existing_exp_keys.add((c, j))

    merged_cfs = list(primary.get("custom_fields") or [])
    existing_cf_keys = {cf.get("field_key") for cf in merged_cfs if isinstance(cf, dict) and cf.get("field_key")}
    for cf in (secondary.get("custom_fields") or []):
        if isinstance(cf, dict):
            k = cf.get("field_key")
            if k and k not in existing_cf_keys:
                merged_cfs.append(cf)
                existing_cf_keys.add(k)

    return {
        "personal_info": merged_pi,
        "experiences": merged_exps,
        "custom_fields": merged_cfs
    }


async def extract_structured_memory_from_text(
    raw_text: str,
    user_id: Optional[int] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Uses configured AI provider (or Groq default) to parse unstructured text into structured profile records.
    Workflow:
    1. Splits extracted content into semantic chunks (Header, Summary, Skills, Experience, Projects, Education, Certifications).
    2. Builds structured multi-chunk representation so LLM receives and analyzes all chunks.
    3. Queries LLM with temperature=0.0 for deterministic, high-fidelity mapping.
    4. Merges and verifies any chunk sections to prevent missing data.
    5. Falls back to chunk-aware heuristic parsing if LLM is offline.
    """
    clean_text = (raw_text or "").strip()
    if not clean_text:
        return {"personal_info": None, "experiences": [], "custom_fields": []}

    from app.ai.provider_manager import AIProviderManager
    user_config = AIProviderManager.get_user_ai_config(db, user_id) if db and user_id else None

    # Step 1: Split into meaningful chunks
    chunks = split_into_semantic_chunks(clean_text)

    # Step 2: Format all chunks into structured prompt
    chunk_blocks = []
    for idx, c in enumerate(chunks, 1):
        chunk_blocks.append(f"=== CHUNK {idx}: [{c['title']}] ===\n{c['content']}")
    all_chunks_text = "\n\n".join(chunk_blocks)

    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"The following document contains {len(chunks)} distinct structured chunks. "
                "Analyze EVERY chunk comprehensively and map all personal identity, contact details, education, "
                "work experiences, projects, technical skills, and certifications into the specified JSON schema:\n\n"
                f"{all_chunks_text[:40000]}"
            )
        }
    ]

    # Temperature 0.0 for deterministic, repeatable extraction results across repeated uploads
    response = await query_groq_llm(messages=messages, temperature=0.0, config=user_config)
    if not response or not isinstance(response, dict):
        raw_res = _fallback_heuristic_extraction(clean_text, chunks=chunks)
        return _clean_extracted_strings(raw_res)

    cleaned_response = _clean_extracted_strings(response)
    primary_result = {
        "personal_info": cleaned_response.get("personal_info"),
        "experiences": cleaned_response.get("experiences") or [],
        "custom_fields": cleaned_response.get("custom_fields") or [],
    }

    # Step 3: Verification & completeness check
    # Check if any major chunk section was missing in the LLM response
    missing_experiences = not primary_result.get("experiences")
    missing_pi = not primary_result.get("personal_info")
    existing_cf_keys = {cf.get("field_key") for cf in primary_result.get("custom_fields", []) if isinstance(cf, dict)}

    if missing_experiences or missing_pi or "projects" not in existing_cf_keys or "certifications" not in existing_cf_keys:
        heuristic_supplements = _fallback_heuristic_extraction(clean_text, chunks=chunks)
        to_merge: Dict[str, Any] = {"personal_info": None, "experiences": [], "custom_fields": []}
        if missing_pi:
            to_merge["personal_info"] = heuristic_supplements.get("personal_info")
        if missing_experiences:
            to_merge["experiences"] = heuristic_supplements.get("experiences") or []
        for cf in heuristic_supplements.get("custom_fields") or []:
            if isinstance(cf, dict) and cf.get("field_key") not in existing_cf_keys:
                to_merge["custom_fields"].append(cf)
        final_merged = merge_extracted_records(primary_result, to_merge)
    else:
        final_merged = primary_result

    return _clean_extracted_strings(final_merged)

    return _clean_extracted_strings(final_merged)


def _fallback_heuristic_extraction(text: str, chunks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Enhanced regex & chunk-aware fallback extractor if external LLM is offline or unconfigured."""
    clean_text = text.strip()
    custom_fields = []
    lines = [l.strip() for l in clean_text.splitlines() if l.strip()]

    # If chunks not provided, compute them
    if chunks is None:
        chunks = split_into_semantic_chunks(clean_text)

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
    deg_match = re.search(r"\b(bachelor(?:'s)?(?:\s+of\s+[A-Za-z\s]+)?|master(?:'s)?(?:\s+of\s+[A-Za-z\s]+)?|ph\.?d\.?|bs|ms|msc|bsc|bba|mba|bscs)\b", clean_text, re.IGNORECASE)
    degree = deg_match.group(0).strip() if deg_match else None

    # Bio / Summary from chunks or text
    bio = None
    for c in chunks:
        title = c.get("title", "").upper()
        if "SUMMARY" in title or "OBJECTIVE" in title or "PROFILE" in title:
            bio = c.get("content", "").strip()[:800]
            break

    # Technical Skills from chunks or text
    skills_text = None
    for c in chunks:
        title = c.get("title", "").upper()
        if "SKILL" in title or "TECHNOLOG" in title:
            skills_text = c.get("content", "").strip().replace("\n", ", ")
            break
    if not skills_text:
        skills_match = re.search(r"(?:technical\s*skills|skills|technologies|expertise|proficiencies)[\s:]+([^\n]+(?:\n[^\n]+){1,3})", clean_text, re.IGNORECASE)
        if skills_match:
            skills_text = re.sub(r"[\r\n]+", ", ", skills_match.group(1)).strip(" ,")
    if skills_text:
        custom_fields.append({
            "field_key": "technical_skills",
            "field_label": "Technical Skills",
            "field_value": skills_text[:500],
            "category": "professional"
        })

    # Projects from chunks
    for c in chunks:
        title = c.get("title", "").upper()
        if "PROJECT" in title:
            proj_text = c.get("content", "").strip().replace("\n", "; ")
            if proj_text:
                custom_fields.append({
                    "field_key": "projects",
                    "field_label": "Projects",
                    "field_value": proj_text[:500],
                    "category": "professional"
                })
            break

    # Certifications from chunks
    for c in chunks:
        title = c.get("title", "").upper()
        if "CERTIF" in title or "COURSE" in title or "LEARNING" in title:
            cert_text = c.get("content", "").strip().replace("\n", "; ")
            if cert_text:
                custom_fields.append({
                    "field_key": "certifications",
                    "field_label": "Certifications",
                    "field_value": cert_text[:500],
                    "category": "professional"
                })
            break

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
    li_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+", clean_text, re.IGNORECASE)
    gh_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+", clean_text, re.IGNORECASE)

    # Heuristic experiences extraction from EXPERIENCE chunk
    experiences = []
    for c in chunks:
        title = c.get("title", "").upper()
        if "EXPERIENCE" in title or "EMPLOYMENT" in title:
            exp_lines = [l.strip() for l in c.get("content", "").splitlines() if l.strip()]
            for l in exp_lines:
                # Look for company/title patterns with pipes or parentheses
                if "|" in l or " - " in l or re.search(r"\b(intern|engineer|developer|lead|coordinator|manager)\b", l, re.IGNORECASE):
                    parts = [p.strip() for p in re.split(r"[|\-–—]", l) if p.strip()]
                    if len(parts) >= 2:
                        comp_clean = re.sub(r"\b\d+\s*(?:months?|years?)\b", "", parts[1], flags=re.IGNORECASE).strip(" ,|")
                        experiences.append({
                            "company": comp_clean or parts[1],
                            "job_title": parts[0],
                            "start_date": "2023-01-01",
                            "end_date": None,
                            "description": l,
                            "skills": None
                        })
                    elif len(parts) == 1:
                        experiences.append({
                            "company": "Organization",
                            "job_title": parts[0],
                            "start_date": "2023-01-01",
                            "end_date": None,
                            "description": l,
                            "skills": None
                        })
            break

    personal_info = {
        "full_name": user_name,
        "email": email,
        "phone": phone,
        "gender": gender,
        "university": university,
        "degree": degree,
        "linkedin_url": li_match.group(0) if li_match else None,
        "github_url": gh_match.group(0) if gh_match else None,
        "bio": bio,
    }

    if not any(personal_info.values()):
        personal_info = None

    return {
        "personal_info": personal_info,
        "experiences": experiences,
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
