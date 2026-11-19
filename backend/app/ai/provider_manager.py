"""
Magic Fill - AI Provider Manager
Central orchestrator for AI provider selection, encrypted credential management,
form field semantic matching, memory extraction, and connection verification.
"""

import base64
import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.ai.base_provider import BaseAIProvider
from app.ai.groq_provider import GroqProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.openrouter_provider import OpenRouterProvider
from app.ai.ollama_provider import OllamaProvider
from app.ai.openai_compatible_provider import OpenAICompatibleProvider
from app.ai.prompts import MATCHING_SYSTEM_PROMPT, EXTRACTION_SYSTEM_PROMPT, CLASSIFICATION_SYSTEM_PROMPT
from app.ai.response_schema import (
    AIProviderConfig,
    AIProviderConfigPublic,
    AIProviderType,
    DEFAULT_MODELS,
    DEFAULT_BASE_URLS,
    TestConnectionResponse,
)
from app.database.database import settings

logger = logging.getLogger("app.ai.provider_manager")


# -----------------------------------------------------------------------------
# Credential Encryption Helpers
# -----------------------------------------------------------------------------

def _get_fernet() -> Fernet:
    """Derives a deterministic 32-byte Fernet key from the application secret."""
    secret = settings.SECRET_KEY or "magic_fill_production_sovereign_secret_key"
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def encrypt_api_key(plain_key: Optional[str]) -> Optional[str]:
    """Encrypts an API key for safe database storage. Returns encrypted string or None."""
    if not plain_key or not plain_key.strip():
        return None
    try:
        f = _get_fernet()
        return f.encrypt(plain_key.strip().encode()).decode()
    except Exception as exc:
        logger.error("Failed to encrypt API key: %s", exc)
        return None


def decrypt_api_key(encrypted_key: Optional[str]) -> Optional[str]:
    """Decrypts a stored API key in memory. Never exposed or logged."""
    if not encrypted_key or not encrypted_key.strip():
        return None
    try:
        f = _get_fernet()
        return f.decrypt(encrypted_key.strip().encode()).decode()
    except Exception as exc:
        logger.error("Failed to decrypt API key: %s", exc)
        return None


def mask_api_key(plain_key: Optional[str]) -> Optional[str]:
    """Returns a masked preview of an API key for safe UI display (e.g. 'sk-...4a2b')."""
    if not plain_key or not plain_key.strip():
        return None
    k = plain_key.strip()
    if len(k) <= 8:
        return "********"
    prefix = k[:4]
    suffix = k[-4:]
    return f"{prefix}...{suffix}"


# -----------------------------------------------------------------------------
# AI Provider Manager
# -----------------------------------------------------------------------------

class AIProviderManager:
    """
    Central Manager for Magic Fill's Bring-Your-Own-LLM (BYO-LLM) architecture.
    Handles provider instantiation, database configuration retrieval, prompt dispatch,
    and hallucination protection.
    """

    @staticmethod
    def get_provider_instance(config: Optional[AIProviderConfig] = None) -> BaseAIProvider:
        """Instantiates the appropriate BaseAIProvider subclass based on configuration."""
        cfg = config or AIProviderConfig(provider=AIProviderType.GROQ.value)
        p_type = (cfg.provider or "groq").lower().strip()

        if p_type == AIProviderType.OPENAI.value:
            return OpenAIProvider(cfg)
        elif p_type == AIProviderType.GEMINI.value:
            return GeminiProvider(cfg)
        elif p_type == AIProviderType.OPENROUTER.value:
            return OpenRouterProvider(cfg)
        elif p_type == AIProviderType.OLLAMA.value:
            return OllamaProvider(cfg)
        elif p_type == AIProviderType.CUSTOM.value:
            return OpenAICompatibleProvider(cfg)
        else:
            # Default to Groq
            return GroqProvider(cfg)

    @classmethod
    def get_user_ai_config(cls, db: Optional[Session], user_id: Optional[int]) -> AIProviderConfig:
        """
        Retrieves user's saved AI configuration from PostgreSQL database.
        If no user or no custom config exists, returns default Groq provider configuration.
        """
        if not db or not user_id:
            return AIProviderConfig(
                provider=AIProviderType.GROQ.value,
                model_name=DEFAULT_MODELS[AIProviderType.GROQ.value],
                api_base_url=DEFAULT_BASE_URLS[AIProviderType.GROQ.value],
                api_key=settings.GROQ_API_KEY,
                is_active=True,
            )

        try:
            from app.database.models import UserAIConfig
            record = db.query(UserAIConfig).filter(UserAIConfig.user_id == user_id).first()
            if record and record.is_active and record.provider:
                plain_key = decrypt_api_key(record.encrypted_api_key)
                return AIProviderConfig(
                    provider=record.provider,
                    model_name=record.model_name or DEFAULT_MODELS.get(record.provider),
                    api_base_url=record.api_base_url or DEFAULT_BASE_URLS.get(record.provider),
                    api_key=plain_key or (settings.GROQ_API_KEY if record.provider == "groq" else None),
                    is_active=record.is_active,
                )
        except Exception as exc:
            logger.warning("Error fetching user AI config for user %s: %s", user_id, exc)

        # Fallback to default Groq
        return AIProviderConfig(
            provider=AIProviderType.GROQ.value,
            model_name=DEFAULT_MODELS[AIProviderType.GROQ.value],
            api_base_url=DEFAULT_BASE_URLS[AIProviderType.GROQ.value],
            api_key=settings.GROQ_API_KEY,
            is_active=True,
        )

    @classmethod
    async def query_llm(
        cls,
        messages: List[Dict[str, str]],
        user_id: Optional[int] = None,
        db: Optional[Session] = None,
        config: Optional[AIProviderConfig] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        timeout_seconds: float = 30.0,
        response_json: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Executes a completion using the resolved AI provider (user custom config or Groq default).
        """
        active_config = config or cls.get_user_ai_config(db, user_id)
        provider = cls.get_provider_instance(active_config)
        return await provider.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
            response_json=response_json,
        )

    @classmethod
    async def test_connection(cls, config: AIProviderConfig) -> TestConnectionResponse:
        """Runs connectivity, authentication, and model accessibility tests for a provider configuration."""
        provider = cls.get_provider_instance(config)
        return await provider.test_connection()

    # -------------------------------------------------------------------------
    # Core Application Workflows (Matching, Extraction, Classification)
    # -------------------------------------------------------------------------

    @classmethod
    async def match_ambiguous_fields(
        cls,
        unresolved_fields: List[Dict[str, Any]],
        user_memory: Dict[str, Any],
        form_context: Optional[str] = None,
        user_id: Optional[int] = None,
        db: Optional[Session] = None,
        config: Optional[AIProviderConfig] = None,
    ) -> List[Dict[str, Any]]:
        """
        Primary AI Matching Workflow: Analyzes detected form input elements using the
        active AI provider and maps them to user memory with hallucination protection.
        """
        if not unresolved_fields or not user_memory:
            return []

        user_prompt = {
            "form_context": form_context or "Web Form",
            "user_memory": user_memory,
            "fields_to_match": unresolved_fields,
        }

        messages = [
            {"role": "system", "content": MATCHING_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_prompt)},
        ]

        active_config = config or cls.get_user_ai_config(db, user_id)
        result = await cls.query_llm(messages=messages, config=active_config)
        if not result or "mappings" not in result or not isinstance(result["mappings"], list):
            return []

        validated_mappings = []
        valid_memory_values, raw_memory_strings = cls._extract_all_memory_tokens(user_memory)
        field_by_id = {str(f.get("field_id")): f for f in unresolved_fields if f.get("field_id")}
        provider_name = active_config.provider.title()

        for item in result["mappings"]:
            field_id = item.get("field_id")
            memory_key = str(item.get("memory_key") or "user_memory")
            value = item.get("value")
            confidence = float(item.get("confidence", 0.0))
            reason = item.get("reason", f"{provider_name} AI semantic match")

            if not field_id or value is None:
                continue

            val_str = str(value).strip()
            if not val_str:
                continue

            target_field = field_by_id.get(str(field_id), {})

            # Grounding check: verify that value is strictly rooted in stored memory
            if cls._is_grounded_in_memory(
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

    @classmethod
    async def extract_structured_memory(
        cls,
        raw_text: str,
        user_id: Optional[int] = None,
        db: Optional[Session] = None,
        config: Optional[AIProviderConfig] = None,
    ) -> Optional[Dict[str, Any]]:
        """Parses unstructured text, resumes, or transcripts into structured memory."""
        if not raw_text or not raw_text.strip():
            return None

        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Extract structured personal memory as a JSON object from the following text:\n\n{raw_text[:8000]}"
            }
        ]

        active_config = config or cls.get_user_ai_config(db, user_id)
        return await cls.query_llm(messages=messages, config=active_config, temperature=0.1)

    @classmethod
    async def classify_field(
        cls,
        field_name: Optional[str],
        label: Optional[str],
        value: str,
        form_context: Optional[str] = None,
        user_id: Optional[int] = None,
        db: Optional[Session] = None,
        config: Optional[AIProviderConfig] = None,
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """Classifies an ambiguous field during live learning."""
        user_payload = {
            "field_name": field_name,
            "label": label,
            "value": value,
            "form_context": form_context or "Job Application Webpage",
        }

        messages = [
            {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload)},
        ]

        active_config = config or cls.get_user_ai_config(db, user_id)
        res = await cls.query_llm(messages=messages, config=active_config, temperature=0.1)
        if res and isinstance(res, dict):
            cat = str(res.get("category", "UNKNOWN")).upper().strip()
            canon_k = res.get("canonical_key")
            field_lbl = res.get("field_label") or label or "Custom Attribute"
            return cat, canon_k, field_lbl

        return "UNKNOWN", None, None

    # -------------------------------------------------------------------------
    # Hallucination Protection & Grounding Verification
    # -------------------------------------------------------------------------

    @staticmethod
    def _extract_all_memory_tokens(data: Any) -> Tuple[set, List[str]]:
        """Collects scalar values and token strings in user memory for grounding checks."""
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

    @classmethod
    def _is_grounded_in_memory(
        cls,
        val: str,
        memory_key: str,
        valid_memory_values: set,
        raw_memory_strings: List[str],
        target_field: Optional[Dict[str, Any]] = None,
        user_memory: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Verifies that the LLM response is anchored in stored user records and not hallucinated."""
        v_lower = val.lower().strip()
        target_field = target_field or {}
        input_type = (target_field.get("input_type") or "").lower()
        options = [str(o).strip().lower() for o in (target_field.get("options") or [])]

        # 1. Exact match in any scalar memory value
        if v_lower in valid_memory_values:
            return True

        # 2. Document reference or file upload or custom memory field
        if (
            memory_key.startswith("documents.")
            or memory_key.startswith("custom_fields.")
            or input_type == "file"
            or "photo" in v_lower
            or "cnic" in v_lower
            or "data:image" in v_lower
            or "passport" in v_lower
            or "resume" in v_lower
            or v_lower == "[attached_document]"
        ):
            return True

        # 3. Dropdown Menu, Radio Buttons, or Choice Buttons with predefined options
        if options:
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
            overlap = val_tokens.intersection(raw_tokens)
            if len(overlap) >= 1:
                return True

        # 8. Token contained within stored memory strings
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
