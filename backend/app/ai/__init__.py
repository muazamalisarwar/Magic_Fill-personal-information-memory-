"""
Magic Fill - AI Module
Provides centralized BYO-LLM abstraction, multi-provider support,
and secure encrypted credential handling.
"""

from app.ai.base_provider import BaseAIProvider
from app.ai.groq_provider import GroqProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.openrouter_provider import OpenRouterProvider
from app.ai.ollama_provider import OllamaProvider
from app.ai.openai_compatible_provider import OpenAICompatibleProvider
from app.ai.provider_manager import (
    AIProviderManager,
    encrypt_api_key,
    decrypt_api_key,
    mask_api_key,
)
from app.ai.response_schema import (
    AIProviderType,
    AIProviderConfig,
    AIProviderConfigPublic,
    AIProviderConfigSaveRequest,
    TestConnectionRequest,
    TestConnectionResponse,
    DEFAULT_MODELS,
    DEFAULT_BASE_URLS,
)
from app.ai.prompts import (
    MATCHING_SYSTEM_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    CLASSIFICATION_SYSTEM_PROMPT,
    TEST_CONNECTION_PROMPT,
)

__all__ = [
    "BaseAIProvider",
    "GroqProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "OpenRouterProvider",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "AIProviderManager",
    "encrypt_api_key",
    "decrypt_api_key",
    "mask_api_key",
    "AIProviderType",
    "AIProviderConfig",
    "AIProviderConfigPublic",
    "AIProviderConfigSaveRequest",
    "TestConnectionRequest",
    "TestConnectionResponse",
    "DEFAULT_MODELS",
    "DEFAULT_BASE_URLS",
    "MATCHING_SYSTEM_PROMPT",
    "EXTRACTION_SYSTEM_PROMPT",
    "CLASSIFICATION_SYSTEM_PROMPT",
    "TEST_CONNECTION_PROMPT",
]
