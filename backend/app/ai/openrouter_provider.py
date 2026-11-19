"""
Magic Fill - OpenRouter Provider
Enables users to connect OpenRouter to access hundreds of open & closed models.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx
from app.ai.base_provider import BaseAIProvider
from app.ai.prompts import TEST_CONNECTION_PROMPT
from app.ai.response_schema import AIProviderConfig, TestConnectionResponse, DEFAULT_MODELS, DEFAULT_BASE_URLS

logger = logging.getLogger("app.ai.openrouter_provider")


class OpenRouterProvider(BaseAIProvider):
    """
    OpenRouter API Provider implementation.
    Standard OpenAI-compatible router with routing headers and broad model support.
    """

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.api_base_url = self.api_base_url or DEFAULT_BASE_URLS["openrouter"]
        self.endpoint_url = f"{self.api_base_url}/chat/completions"
        self.model_name = self.model_name or DEFAULT_MODELS["openrouter"]

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://magicfill.ai",
            "X-Title": "Magic Fill",
            "Content-Type": "application/json",
        }

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        timeout_seconds: float = 35.0,
        response_json: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Sends chat completion to OpenRouter with JSON response format."""
        if not self.api_key:
            logger.warning("No OpenRouter API key provided.")
            return None

        current_model = model or self.model_name
        headers = self._get_headers()
        payload: Dict[str, Any] = {
            "model": current_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 3072,
        }
        if response_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                res = await client.post(self.endpoint_url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    return self.clean_and_parse_json(content)
                else:
                    logger.warning("OpenRouter error HTTP %d: %s", res.status_code, res.text[:150])
                    return None
        except Exception as exc:
            logger.warning("OpenRouter exception: %s", self.sanitize_error(exc))
            return None

    async def test_connection(self) -> TestConnectionResponse:
        """Verifies OpenRouter API key and model availability."""
        if not self.api_key or not self.api_key.strip():
            return TestConnectionResponse(
                success=False,
                message="OpenRouter API key is missing. Please enter your API key (starts with 'sk-or-').",
                provider=self.provider_name,
                model_name=self.model_name,
                error_code="MISSING_API_KEY"
            )

        start_time = time.time()
        headers = self._get_headers()
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": TEST_CONNECTION_PROMPT}],
            "response_format": {"type": "json_object"},
            "max_tokens": 50,
        }

        try:
            async with httpx.AsyncClient(timeout=16.0) as client:
                res = await client.post(self.endpoint_url, headers=headers, json=payload)
                latency = round((time.time() - start_time) * 1000, 1)

                if res.status_code == 200:
                    return TestConnectionResponse(
                        success=True,
                        message=f"Connected successfully to OpenRouter ({self.model_name}) in {latency}ms!",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency
                    )
                elif res.status_code == 401:
                    return TestConnectionResponse(
                        success=False,
                        message="Invalid OpenRouter API key. Check your key at openrouter.ai/keys.",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency,
                        error_code="UNAUTHORIZED"
                    )
                elif res.status_code == 402:
                    return TestConnectionResponse(
                        success=False,
                        message="Insufficient OpenRouter credits. Add balance at openrouter.ai/credits.",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency,
                        error_code="INSUFFICIENT_CREDITS"
                    )
                elif res.status_code == 404:
                    return TestConnectionResponse(
                        success=False,
                        message=f"Model '{self.model_name}' was not found on OpenRouter.",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency,
                        error_code="MODEL_NOT_FOUND"
                    )
                else:
                    return TestConnectionResponse(
                        success=False,
                        message=f"OpenRouter returned HTTP {res.status_code}: {res.text[:120]}",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency,
                        error_code=f"HTTP_{res.status_code}"
                    )
        except Exception as exc:
            return TestConnectionResponse(
                success=False,
                message=self.sanitize_error(exc),
                provider=self.provider_name,
                model_name=self.model_name,
                error_code="NETWORK_ERROR"
            )
