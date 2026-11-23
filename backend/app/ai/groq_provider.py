"""
Magic Fill - Groq AI Provider
Default built-in AI provider for Magic Fill. Zero user configuration required.
Features automatic multi-model fallback across high-capacity models.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx
from app.ai.base_provider import BaseAIProvider
from app.ai.prompts import TEST_CONNECTION_PROMPT
from app.ai.response_schema import AIProviderConfig, TestConnectionResponse, DEFAULT_MODELS, DEFAULT_BASE_URLS
from app.database.database import settings

logger = logging.getLogger("app.ai.groq_provider")


class GroqProvider(BaseAIProvider):
    """
    Groq AI Provider implementation using Groq's high-speed inference API.
    Used by default across Magic Fill with zero setup needed.
    """

    def __init__(self, config: Optional[AIProviderConfig] = None):
        cfg = config or AIProviderConfig(provider="groq")
        super().__init__(cfg)
        self.api_base_url = self.api_base_url or DEFAULT_BASE_URLS["groq"]
        self.endpoint_url = f"{self.api_base_url}/chat/completions"
        self.api_key = self.api_key or settings.GROQ_API_KEY
        self.model_name = self.model_name or settings.GROQ_MODEL or DEFAULT_MODELS["groq"]

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        timeout_seconds: float = 25.0,
        response_json: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Calls Groq Chat Completions API with multi-model fallback."""
        if not self.api_key or self.api_key.startswith("gsk_your_groq_api_key"):
            logger.debug("Groq API key is not configured or using placeholder; skipping.")
            return None

        # Priority candidate models: requested model first, then configured, then fallbacks
        candidate_models: List[str] = []
        target_model = model or self.model_name
        supported_candidates = ["qwen/qwen3.8-27b", "allam-2-7b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
        if target_model and target_model in supported_candidates:
            candidate_models.append(target_model)
        for m in supported_candidates:
            if m not in candidate_models:
                candidate_models.append(m)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Prepare messages ensuring valid JSON formatting instruction
        prepared_messages = [dict(m) for m in messages]
        if response_json:
            has_json = any("json" in (m.get("content") or "").lower() for m in prepared_messages)
            if not has_json and prepared_messages:
                last_msg = dict(prepared_messages[-1])
                last_msg["content"] = (last_msg.get("content") or "") + "\n\nRespond strictly in valid JSON format."
                prepared_messages[-1] = last_msg

        per_model_timeout = httpx.Timeout(timeout=min(timeout_seconds, 6.0), connect=3.0)
        for current_model in candidate_models:
            payload: Dict[str, Any] = {
                "model": current_model,
                "messages": prepared_messages,
                "temperature": temperature,
                "max_tokens": 4096,
            }
            if response_json:
                payload["response_format"] = {"type": "json_object"}

            try:
                async with httpx.AsyncClient(timeout=per_model_timeout) as client:
                    response = await client.post(self.endpoint_url, headers=headers, json=payload)
                    # If 400 error about json_object response_format, retry without response_format
                    if response.status_code == 400 and response_json and "json" in response.text.lower():
                        logger.debug("Retrying Groq model '%s' without explicit response_format...", current_model)
                        payload.pop("response_format", None)
                        response = await client.post(self.endpoint_url, headers=headers, json=payload)

                    if response.status_code == 200:
                        data = response.json()
                        content = data["choices"][0]["message"]["content"]
                        parsed = self.clean_and_parse_json(content)
                        if parsed is not None:
                            return parsed
                    elif response.status_code in (429, 404, 503, 502):
                        logger.warning(
                            "Groq model '%s' returned HTTP %d, trying fallback candidate...",
                            current_model, response.status_code
                        )
                        continue
                    else:
                        logger.warning("Groq API error on model '%s': HTTP %d: %s", current_model, response.status_code, response.text[:120])
                        continue
            except httpx.ConnectTimeout as exc:
                logger.warning("Groq host connection timed out; failing fast to local grounded engine: %s", exc)
                break
            except (httpx.TimeoutException, json.JSONDecodeError) as exc:
                logger.warning("Groq model '%s' timed out or JSON error: %s", current_model, str(exc))
                continue
            except Exception as exc:
                logger.warning("Error with Groq model '%s': %s", current_model, str(exc))
                continue

        logger.error("All Groq model candidates failed to return a valid JSON response.")
        return None

    async def test_connection(self) -> TestConnectionResponse:
        """Verifies Groq API key validity and model accessibility."""
        if not self.api_key or self.api_key.startswith("gsk_your_groq_api_key"):
            return TestConnectionResponse(
                success=False,
                message="No Groq API key configured. Provide an API key or configure GROQ_API_KEY in backend environment.",
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
            "messages": [
                {"role": "user", "content": TEST_CONNECTION_PROMPT}
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 50,
        }

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.post(self.endpoint_url, headers=headers, json=payload)
                latency = round((time.time() - start_time) * 1000, 1)

                if res.status_code == 200:
                    return TestConnectionResponse(
                        success=True,
                        message=f"Connected successfully to Groq ({self.model_name}) in {latency}ms!",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency
                    )
                elif res.status_code == 401:
                    return TestConnectionResponse(
                        success=False,
                        message="Invalid Groq API key. Please check your key at console.groq.com/keys.",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency,
                        error_code="UNAUTHORIZED"
                    )
                elif res.status_code == 404:
                    return TestConnectionResponse(
                        success=False,
                        message=f"Model '{self.model_name}' not found on Groq. Try 'llama-3.3-70b-versatile'.",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency,
                        error_code="MODEL_NOT_FOUND"
                    )
                elif res.status_code == 429:
                    return TestConnectionResponse(
                        success=False,
                        message="Groq rate limit reached or quota exceeded.",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency,
                        error_code="RATE_LIMIT"
                    )
                else:
                    return TestConnectionResponse(
                        success=False,
                        message=f"Groq API returned HTTP {res.status_code}: {res.text[:120]}",
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
