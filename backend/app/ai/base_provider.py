"""
Magic Fill - Base AI Provider Abstraction
Defines the common interface, resilient JSON cleaning, error sanitization,
and shared connection testing methods for all LLM providers.
"""

from abc import ABC, abstractmethod
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional
from app.ai.response_schema import AIProviderConfig, TestConnectionResponse

logger = logging.getLogger("app.ai.base_provider")


class BaseAIProvider(ABC):
    """
    Abstract Base Class for all AI providers in Magic Fill.
    Standardizes chat completion, structured JSON parsing, and test-connection logic.
    """

    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.provider_name = config.provider
        self.model_name = config.model_name
        self.api_base_url = (config.api_base_url or "").rstrip("/")
        self.api_key = config.api_key

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        timeout_seconds: float = 30.0,
        response_json: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Executes an asynchronous chat completion request and returns a parsed JSON dict.
        Must return None or raise an exception on failure.
        """
        pass

    @abstractmethod
    async def test_connection(self) -> TestConnectionResponse:
        """
        Verifies API endpoint reachability, credential validity, and model accessibility.
        Returns a structured TestConnectionResponse. Never leaks raw API keys.
        """
        pass

    # -------------------------------------------------------------------------
    # Shared Helper Methods
    # -------------------------------------------------------------------------

    @staticmethod
    def clean_and_parse_json(raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Robustly extracts and parses JSON from LLM output.
        Handles markdown code fences (```json ... ```), extra prose, and trailing commas.
        """
        if not raw_text or not isinstance(raw_text, str):
            return None

        text = raw_text.strip()

        # 1. Direct parse attempt
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. Extract content within ```json ... ``` or ``` ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fence_match:
            fence_content = fence_match.group(1).strip()
            try:
                return json.loads(fence_content)
            except json.JSONDecodeError:
                text = fence_content

        # 3. Locate the outermost curly braces { ... }
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            substring = text[start_idx : end_idx + 1].strip()
            try:
                return json.loads(substring)
            except json.JSONDecodeError:
                # Clean common trailing comma errors before closing braces
                cleaned_comma = re.sub(r",\s*([\}\]])", r"\1", substring)
                try:
                    return json.loads(cleaned_comma)
                except json.JSONDecodeError:
                    pass

        logger.warning("Failed to extract valid JSON from LLM response preview: %s", raw_text[:200])
        return None

    def sanitize_error(self, exc: Exception) -> str:
        """
        Strips API keys, passwords, and sensitive credentials from error messages.
        Returns user-friendly diagnostics.
        """
        err_msg = str(exc)
        if self.api_key and len(self.api_key) > 6:
            err_msg = err_msg.replace(self.api_key, f"{self.api_key[:3]}...{self.api_key[-3:]}")

        # Remove authorization headers or key query parameters
        err_msg = re.sub(r"key=[A-Za-z0-9_\-]+", "key=***", err_msg)
        err_msg = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer ***", err_msg)

        # Standardize common error scenarios
        err_lower = err_msg.lower()
        if "401" in err_msg or "unauthorized" in err_lower or "invalid api key" in err_lower:
            return f"Authentication failed: The API key for {self.provider_name.title()} is invalid or expired."
        if "403" in err_msg or "forbidden" in err_lower:
            return f"Access forbidden: Your account lacks permission for model '{self.model_name}' on {self.provider_name.title()}."
        if "404" in err_msg or "not found" in err_lower:
            return f"Model or endpoint not found: '{self.model_name}' is not recognized or unavailable on {self.provider_name.title()}."
        if "429" in err_msg or "rate limit" in err_lower or "quota" in err_lower:
            return f"Rate limit or quota exceeded on {self.provider_name.title()}. Check your provider billing or limits."
        if "connect" in err_lower and ("refused" in err_lower or "failed" in err_lower):
            return f"Connection refused: Unable to connect to {self.api_base_url or self.provider_name}. Verify that the service is running."
        if "timeout" in err_lower or "timed out" in err_lower:
            return f"Request timed out while waiting for {self.provider_name.title()} ({self.model_name})."

        return err_msg
