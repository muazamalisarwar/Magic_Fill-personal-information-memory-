"""
Magic Fill - OpenAI Provider
Enables users to connect their own OpenAI API key (gpt-4o-mini, gpt-4o, etc.).
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx
from app.ai.base_provider import BaseAIProvider
from app.ai.prompts import TEST_CONNECTION_PROMPT
from app.ai.response_schema import AIProviderConfig, TestConnectionResponse, DEFAULT_MODELS, DEFAULT_BASE_URLS

logger = logging.getLogger("app.ai.openai_provider")


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI API Provider implementation.
    Supports official OpenAI endpoints, gpt-4o-mini, gpt-4o, and other chat models.
    """

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.api_base_url = self.api_base_url or DEFAULT_BASE_URLS["openai"]
        self.endpoint_url = f"{self.api_base_url}/chat/completions"
        self.model_name = self.model_name or DEFAULT_MODELS["openai"]

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        timeout_seconds: float = 30.0,
        response_json: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Sends chat completion to OpenAI with JSON object response format."""
        if not self.api_key:
            logger.warning("No OpenAI API key provided.")
            return None

        current_model = model or self.model_name
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
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
                    logger.warning("OpenAI API returned HTTP %d: %s", res.status_code, res.text[:150])
                    return None
        except Exception as exc:
            logger.warning("Error communicating with OpenAI (%s): %s", current_model, self.sanitize_error(exc))
            return None

    async def test_connection(self) -> TestConnectionResponse:
        """Tests API key and model accessibility on OpenAI."""
        if not self.api_key or not self.api_key.strip():
            return TestConnectionResponse(
                success=False,
                message="OpenAI API key is missing. Please enter your API key (starts with 'sk-').",
                provider=self.provider_name,
                model_name=self.model_name,
                error_code="MISSING_API_KEY"
            )

        start_time = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": TEST_CONNECTION_PROMPT}],
            "response_format": {"type": "json_object"},
            "max_tokens": 50,
        }

        try:
            async with httpx.AsyncClient(timeout=14.0) as client:
                res = await client.post(self.endpoint_url, headers=headers, json=payload)
                latency = round((time.time() - start_time) * 1000, 1)

                if res.status_code == 200:
                    return TestConnectionResponse(
                        success=True,
                        message=f"Connected successfully to OpenAI ({self.model_name}) in {latency}ms!",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency
                    )
                elif res.status_code == 401:
                    return TestConnectionResponse(
                        success=False,
                        message="Invalid OpenAI API key. Check your key at platform.openai.com/api-keys.",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency,
                        error_code="UNAUTHORIZED"
                    )
                elif res.status_code == 404:
                    return TestConnectionResponse(
                        success=False,
                        message=f"OpenAI model '{self.model_name}' not found or not accessible with your key.",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency,
                        error_code="MODEL_NOT_FOUND"
                    )
                elif res.status_code == 429:
                    return TestConnectionResponse(
                        success=False,
                        message="OpenAI rate limit reached or insufficient account credits.",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency,
                        error_code="RATE_LIMIT"
                    )
                else:
                    return TestConnectionResponse(
                        success=False,
                        message=f"OpenAI error (HTTP {res.status_code}): {res.text[:120]}",
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
