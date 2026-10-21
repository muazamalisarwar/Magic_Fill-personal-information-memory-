import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx
from app.database.database import settings

logger = logging.getLogger("app.services.groq_service")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


async def query_groq_llm(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.1,
    timeout_seconds: float = 12.0,
) -> Optional[Dict[str, Any]]:
    """
    Asynchronously calls the Groq Chat Completions API with JSON mode enabled.
    Gracefully falls back to None if GROQ_API_KEY is not configured or an error occurs.
    """
    api_key = settings.GROQ_API_KEY
    if not api_key or api_key.startswith("gsk_your_groq_api_key"):
        logger.debug("Groq API key is not configured or using placeholder; skipping LLM call.")
        return None

    selected_model = model or settings.GROQ_MODEL
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": selected_model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": temperature,
        "max_tokens": 3072,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(GROQ_API_URL, headers=headers, json=payload)
            if response.status_code != 200:
                logger.warning(
                    "Groq API returned HTTP status %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                return None

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return parsed
    except httpx.TimeoutException:
        logger.warning("Groq API request timed out after %.1fs", timeout_seconds)
        return None
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse Groq API response as JSON: %s", str(exc))
        return None
    except Exception as exc:
        logger.warning("Unexpected error communicating with Groq API: %s", str(exc))
        return None


async def match_ambiguous_fields_with_groq(
    unresolved_fields: List[Dict[str, Any]],
    user_memory: Dict[str, Any],
    form_context: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Primary AI Engine: Uses Groq LLM to analyze all detected website input fields
    and decide which stored user memory attributes belong in each field.
    Supports all 10 form element types:
    1. Text Input
    2. Dropdown Menu
    3. Radio Buttons
    4. Checkboxes
    5. File Upload
    6. Text Area
    7. Date Picker
    8. Toggle / Switch
    9. Slider
    10. Buttons
    Ensures that values are strictly grounded in user_memory and never hallucinated.
    """
    if not unresolved_fields or not user_memory:
        return []

    system_prompt = (
        "You are Magic Fill's Core AI Form Matching Engine. Your mission is to analyze "
        "ALL detected input fields on a web page and decide which value from User Memory "
        "should be written into each field.\n\n"
        "CORE RULES & MULTI-CONTROL INSTRUCTIONS:\n"
        "1. STRICT TRUTHFULNESS & GROUNDING: You must NEVER hallucinate or invent fake identity data. "
        "Every mapped value must be grounded in the provided User Memory.\n"
        "2. ALL 10 FORM CONTROL TYPES:\n"
        "   - Text Input: Match exact or normalized scalar string from user memory.\n"
        "   - Dropdown Menu (select / select-one): When 'options' are provided, you MUST pick "
        "     the exact option string from the options list that best matches the user's data "
        "     (e.g., if user has degree 'BS Computer Science', select 'Bachelor of Science'; "
        "     if gender is 'Male', select 'Male' or 'M').\n"
        "   - Radio Buttons: When field input_type is 'radio' or has radio options, select the exact "
        "     option value/label corresponding to the user's data (e.g. work authorization, gender, job type).\n"
        "   - Checkboxes: Return true or false (or 'true' / 'false' / 1 / 0) based on user memory.\n"
        "   - File Upload: When input_type is 'file', match to the relevant document key in "
        "     user_memory.documents (e.g. 'documents.profile_photo', 'documents.cnic_front', 'documents.cnic_back').\n"
        "   - Text Area: For bio, summary, cover letter, or notes, synthesize a concise, professional summary "
        "     (1-3 sentences) strictly derived from the user's experiences, title, and skills.\n"
        "   - Date Picker: Format dates as ISO 'YYYY-MM-DD' (e.g. '2001-05-14').\n"
        "   - Toggle / Switch: Return true or false indicating user preference or status.\n"
        "   - Slider: When input_type is 'range', return a numeric integer/float within min/max reflecting user data "
        "     (e.g. calculated total years of experience from experiences list).\n"
        "   - Choice Buttons: Return the exact button label or value to select.\n"
        "3. SEMANTIC SYNONYMS & NATURAL REASONING:\n"
        "   - 'Salary' <-> 'Monthly Salary' / 'Current Salary' / 'Expected Pay' / 'Income' / 'Compensation'\n"
        "   - 'First Name' <-> 'Given Name' / 'Applicant First Name' / 'Forename'\n"
        "   - 'Last Name' <-> 'Surname' / 'Family Name'\n"
        "   - 'Full Name' <-> 'Complete Legal Name' / 'Applicant Name'\n"
        "   - 'Father Name' <-> 'Father's Name' / 'Parent's Name'\n"
        "   - 'Phone' <-> 'Mobile' / 'Cell Number' / 'Contact Number'\n"
        "   - 'University' <-> 'Institution' / 'College' / 'Alma Mater'\n"
        "   - 'CNIC' <-> 'National ID' / 'ID Number'\n"
        "   - 'Photo' / 'Avatar' <-> 'Profile Picture' / 'Attach Photo'\n"
        "4. ONLY leave a field unmapped if User Memory has no relevant or derivable data for it.\n"
        "5. Return a valid JSON object matching this schema:\n"
        "   {\n"
        '     "mappings": [\n'
        '       {\n'
        '         "field_id": "field id from fields_to_match",\n'
        '         "memory_key": "path in user_memory (e.g. personal_info.full_name, custom_fields.salary, experiences)",\n'
        '         "value": "exact grounded value to fill into field",\n'
        '         "confidence": 0.95,\n'
        '         "reason": "Clear explanation of semantic match"\n'
        '       }\n'
        '     ]\n'
        '   }'
    )

    user_prompt = {
        "form_context": form_context or "Web Form",
        "user_memory": user_memory,
        "fields_to_match": unresolved_fields,
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_prompt)},
    ]

    result = await query_groq_llm(messages=messages)
    if not result or "mappings" not in result or not isinstance(result["mappings"], list):
        return []

    validated_mappings = []
    # Build set of all stringified values present in user memory for hallucination protection
    valid_memory_values, raw_memory_strings = _extract_all_memory_tokens(user_memory)
    field_by_id = {str(f.get("field_id")): f for f in unresolved_fields if f.get("field_id")}

    for item in result["mappings"]:
        field_id = item.get("field_id")
        memory_key = str(item.get("memory_key") or "user_memory")
        value = item.get("value")
        confidence = float(item.get("confidence", 0.0))
        reason = item.get("reason", "Groq LLM semantic match")

        if not field_id or value is None:
            continue

        val_str = str(value).strip()
        if not val_str:
            continue

        target_field = field_by_id.get(str(field_id), {})

        # Grounding check: verify that the value is rooted in user_memory or valid option for the field
        if _is_grounded_in_memory(
            val=val_str,
            memory_key=memory_key,
            valid_memory_values=valid_memory_values,
            raw_memory_strings=raw_memory_strings,
            target_field=target_field,
            user_memory=user_memory,
        ):
            validated_mappings.append({
                "field_id": str(field_id),
                "memory_key": memory_key,
                "value": val_str,
                "confidence": min(max(confidence, 0.5), 1.0),
                "reason": str(reason),
                "source": "llm",
            })

    return validated_mappings


def _extract_all_memory_tokens(data: Any) -> tuple[set, list[str]]:
    """Collects scalar values and token strings in user memory for hallucination protection."""
    values = set()
    raw_strings = []

    def _recurse(node: Any):
        if isinstance(node, dict):
            for v in node.values():
                _recurse(v)
        elif isinstance(node, list):
            for item in node:
                _recurse(item)
        elif node is not None:
            s = str(node).strip()
            if s:
                values.add(s.lower())
                raw_strings.append(s.lower())

    _recurse(data)
    return values, raw_strings


def _is_grounded_in_memory(
    val: str,
    memory_key: str,
    valid_memory_values: set,
    raw_memory_strings: list[str],
    target_field: Optional[Dict[str, Any]] = None,
    user_memory: Optional[Dict[str, Any]] = None,
) -> bool:
    """Verifies that the LLM output is grounded in actual user memory and not hallucinated."""
    v_lower = val.lower().strip()
    target_field = target_field or {}
    input_type = (target_field.get("input_type") or "").lower()
    options = [str(o).strip().lower() for o in (target_field.get("options") or [])]

    # 1. Exact match in any scalar memory value
    if v_lower in valid_memory_values:
        return True

    # 2. Document reference or file upload
    if (
        memory_key.startswith("documents.")
        or input_type == "file"
        or "photo" in v_lower
        or "cnic" in v_lower
        or "data:image" in v_lower
        or "passport" in v_lower
        or "resume" in v_lower
    ):
        return True

    # 3. Dropdown Menu, Radio Buttons, or Choice Buttons with predefined options
    if options:
        # Check if LLM picked one of the available options
        if any(v_lower == opt or v_lower in opt or opt in v_lower for opt in options):
            return True

    # 4. Checkbox, Switch, or Toggle booleans
    if input_type in ("checkbox", "switch", "toggle") or v_lower in ("true", "false", "yes", "no", "1", "0", "on", "off"):
        return True

    # 5. Slider or Numeric ranges
    if input_type in ("range", "number", "slider") or val.replace(".", "", 1).isdigit():
        return True

    # 6. Date Picker (e.g. YYYY-MM-DD or partial date)
    if input_type in ("date", "datetime-local") or re.match(r"^\d{4}-\d{2}(-\d{2})?$", val):
        return True

    # 7. Textarea / Multi-sentence professional summary: verify semantic overlap
    if input_type == "textarea" or len(val) > 40:
        val_tokens = set(re.findall(r"\w{3,}", v_lower))
        raw_tokens = set()
        for raw in raw_memory_strings:
            raw_tokens.update(re.findall(r"\w{3,}", raw))
        # If there is meaningful overlap with stored skills, roles, or company names
        overlap = val_tokens.intersection(raw_tokens)
        if len(overlap) >= 1:
            return True

    # 8. Word or token contained within any stored memory string
    for raw in raw_memory_strings:
        if v_lower in raw.split() or v_lower in raw:
            return True

    # 9. Digits match for phone numbers or CNIC
    digits_val = "".join(filter(str.isdigit, v_lower))
    if len(digits_val) >= 4:
        for raw in raw_memory_strings:
            digits_raw = "".join(filter(str.isdigit, raw))
            if digits_raw and (digits_val in digits_raw or digits_raw in digits_val):
                return True

    return False

