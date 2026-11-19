"""
Magic Fill - Groq Service (Backwards-Compatible AI Adapter)
Routes through the unified AIProviderManager while maintaining complete
compatibility with existing callers, routers, and unit test patches.
"""

import logging
from typing import Any, Dict, List, Optional
from app.ai.provider_manager import AIProviderManager
from app.ai.response_schema import AIProviderConfig, AIProviderType
from app.database.database import settings

logger = logging.getLogger("app.services.groq_service")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


async def query_groq_llm(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.1,
    timeout_seconds: float = 25.0,
    config: Optional[AIProviderConfig] = None,
) -> Optional[Dict[str, Any]]:
    """
    Asynchronously queries the active AI provider (defaults to Groq).
    Maintains compatibility with tests and callers expecting query_groq_llm.
    """
    target_config = config or AIProviderConfig(
        provider=AIProviderType.GROQ.value,
        model_name=model or settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY
    )
    return await AIProviderManager.query_llm(
        messages=messages,
        config=target_config,
        model=model,
        temperature=temperature,
        timeout_seconds=timeout_seconds,
    )


async def match_ambiguous_fields_with_groq(
    unresolved_fields: List[Dict[str, Any]],
    user_memory: Dict[str, Any],
    form_context: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Optional[Any] = None,
    config: Optional[AIProviderConfig] = None,
) -> List[Dict[str, Any]]:
    """
    Analyzes detected website input fields using the unified AI Provider Manager.
    Supports all 10 form element types and applies strict grounding checks.
    """
    return await AIProviderManager.match_ambiguous_fields(
        unresolved_fields=unresolved_fields,
        user_memory=user_memory,
        form_context=form_context,
        user_id=user_id,
        db=db,
        config=config,
    )


# Expose grounding verification functions for test compatibility
_extract_all_memory_tokens = AIProviderManager._extract_all_memory_tokens
_is_grounded_in_memory = AIProviderManager._is_grounded_in_memory
