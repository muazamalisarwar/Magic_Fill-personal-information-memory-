"""
Magic Fill - Custom OpenAI-Compatible Provider
Allows users to connect any OpenAI-compatible API endpoint (vLLM, LM Studio,
LocalAI, Together AI, DeepSeek, self-hosted proxies, etc.).
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx
from app.ai.base_provider import BaseAIProvider
from app.ai.prompts import TEST_CONNECTION_PROMPT
from app.ai.response_schema import AIProviderConfig, TestConnectionResponse

logger = logging.getLogger("app.ai.openai_compatible_provider")


class OpenAICompatibleProvider(BaseAIProvider):
    """
    Generic OpenAI-compatible API Provider.
    Works with any server adhering to the /chat/completions specification.
    """

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        base = self.api_base_url.rstrip("/")
        # Auto-append /chat/completions if base URL does not end with it
        if base.endswith("/chat/completions"):
            self.endpoint_url = base
        elif base.endswith("/v1"):
            self.endpoint_url = f"{base}/chat/completions"
        else:
            self.endpoint_url = f"{base}/chat/completions" if base else ""

        self.model_name = self.model_name or "default-model"

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        timeout_seconds: float = 35.0,
        response_json: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Sends chat completion to custom OpenAI-compatible endpoint."""
        if not self.endpoint_url:
            logger.warning("Custom API base URL is not configured.")
            return None

        current_model = model or self.model_name
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

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
                    choices = data.get("choices") or []
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        return self.clean_and_parse_json(content)
                else:
                    logger.warning("Custom API error HTTP %d: %s", res.status_code, res.text[:120])
                    return None
        except Exception as exc:
            logger.warning("Custom API exception: %s", self.sanitize_error(exc))
            return None

    async def test_connection(self) -> TestConnectionResponse:
        """Verifies reachability and completion on custom OpenAI-compatible endpoint."""
        if not self.endpoint_url:
            return TestConnectionResponse(
                success=False,
                message="API Base URL is required for custom OpenAI-compatible providers.",
                provider=self.provider_name,
                model_name=self.model_name,
                error_code="MISSING_BASE_URL"
            )

        start_time = time.time()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": TEST_CONNECTION_PROMPT}],
            "max_tokens": 50,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(self.endpoint_url, headers=headers, json=payload)
                latency = round((time.time() - start_time) * 1000, 1)

                if res.status_code == 200:
                    return TestConnectionResponse(
                        success=True,
                        message=f"Connected successfully to Custom API ({self.model_name}) in {latency}ms!",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency
                    )
                else:
                    return TestConnectionResponse(
                        success=False,
                        message=f"Custom API returned HTTP {res.status_code}: {res.text[:120]}",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency,
                        error_code=f"HTTP_{res.status_code}"
                    )
        except httpx.ConnectError:
            return TestConnectionResponse(
                success=False,
                message=f"Connection refused at {self.endpoint_url}. Verify that your custom endpoint is running and accessible.",
                provider=self.provider_name,
                model_name=self.model_name,
                error_code="CONNECTION_REFUSED"
            )
        except Exception as exc:
            return TestConnectionResponse(
                success=False,
                message=self.sanitize_error(exc),
                provider=self.provider_name,
                model_name=self.model_name,
                error_code="NETWORK_ERROR"
            )
