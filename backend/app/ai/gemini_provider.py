"""
Magic Fill - Google Gemini Provider
Enables users to connect their Google Gemini API key (gemini-1.5-flash, gemini-2.0-flash, etc.).
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx
from app.ai.base_provider import BaseAIProvider
from app.ai.prompts import TEST_CONNECTION_PROMPT
from app.ai.response_schema import AIProviderConfig, TestConnectionResponse, DEFAULT_MODELS, DEFAULT_BASE_URLS

logger = logging.getLogger("app.ai.gemini_provider")


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini Provider implementation.
    Uses Google's native REST API with responseMimeType='application/json'
    for guaranteed structured JSON output.
    """

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.api_base_url = self.api_base_url or DEFAULT_BASE_URLS["gemini"]
        self.model_name = self.model_name or DEFAULT_MODELS["gemini"]

    def _build_native_payload(self, messages: List[Dict[str, str]], temperature: float) -> Dict[str, Any]:
        """Converts OpenAI message list into Google Gemini generateContent payload."""
        system_texts = []
        contents = []

        for m in messages:
            role = m.get("role", "user").lower()
            text = m.get("content", "")
            if role == "system":
                system_texts.append(text)
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": text}]})
            else:
                contents.append({"role": "user", "parts": [{"text": text}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
                "maxOutputTokens": 3072,
            }
        }
        if system_texts:
            payload["systemInstruction"] = {
                "parts": [{"text": "\n\n".join(system_texts)}]
            }

        return payload

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        timeout_seconds: float = 30.0,
        response_json: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Executes a chat completion via Google Gemini REST API."""
        if not self.api_key:
            logger.warning("No Gemini API key provided.")
            return None

        current_model = model or self.model_name
        # Clean model name if user provided e.g. 'models/gemini-1.5-flash'
        clean_model = current_model.replace("models/", "")

        # Check if user specified custom OpenAI-compatible endpoint
        if "openai" in self.api_base_url:
            return await self._call_openai_compatible(messages, clean_model, temperature, timeout_seconds)

        url = f"{self.api_base_url}/models/{clean_model}:generateContent?key={self.api_key}"
        payload = self._build_native_payload(messages, temperature)

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                res = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates") or []
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            raw_content = parts[0].get("text", "")
                            return self.clean_and_parse_json(raw_content)
                else:
                    logger.warning("Gemini API error HTTP %d: %s", res.status_code, res.text[:150])
                    return None
        except Exception as exc:
            logger.warning("Error with Gemini (%s): %s", clean_model, self.sanitize_error(exc))
            return None

        return None

    async def _call_openai_compatible(
        self, messages: List[Dict[str, str]], model: str, temperature: float, timeout_seconds: float
    ) -> Optional[Dict[str, Any]]:
        """Fallback for Gemini's OpenAI-compatible endpoint."""
        endpoint = f"{self.api_base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                res = await client.post(endpoint, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return self.clean_and_parse_json(data["choices"][0]["message"]["content"])
        except Exception:
            pass
        return None

    async def test_connection(self) -> TestConnectionResponse:
        """Verifies Gemini API key validity and model accessibility."""
        if not self.api_key or not self.api_key.strip():
            return TestConnectionResponse(
                success=False,
                message="Google Gemini API key is missing. Please enter your API key (from Google AI Studio).",
                provider=self.provider_name,
                model_name=self.model_name,
                error_code="MISSING_API_KEY"
            )

        start_time = time.time()
        clean_model = self.model_name.replace("models/", "")
        url = f"{self.api_base_url}/models/{clean_model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": TEST_CONNECTION_PROMPT}]}],
            "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 50}
        }

        try:
            async with httpx.AsyncClient(timeout=14.0) as client:
                res = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                latency = round((time.time() - start_time) * 1000, 1)

                if res.status_code == 200:
                    return TestConnectionResponse(
                        success=True,
                        message=f"Connected successfully to Google Gemini ({clean_model}) in {latency}ms!",
                        provider=self.provider_name,
                        model_name=clean_model,
                        latency_ms=latency
                    )
                elif res.status_code in (400, 403):
                    return TestConnectionResponse(
                        success=False,
                        message="Invalid Google Gemini API key. Check your key at aistudio.google.com/app/apikey.",
                        provider=self.provider_name,
                        model_name=clean_model,
                        latency_ms=latency,
                        error_code="UNAUTHORIZED"
                    )
                elif res.status_code == 404:
                    return TestConnectionResponse(
                        success=False,
                        message=f"Gemini model '{clean_model}' was not found. Try 'gemini-1.5-flash'.",
                        provider=self.provider_name,
                        model_name=clean_model,
                        latency_ms=latency,
                        error_code="MODEL_NOT_FOUND"
                    )
                elif res.status_code == 429:
                    return TestConnectionResponse(
                        success=False,
                        message="Google Gemini rate limit reached. Please wait or check your quota.",
                        provider=self.provider_name,
                        model_name=clean_model,
                        latency_ms=latency,
                        error_code="RATE_LIMIT"
                    )
                else:
                    return TestConnectionResponse(
                        success=False,
                        message=f"Gemini API returned HTTP {res.status_code}: {res.text[:120]}",
                        provider=self.provider_name,
                        model_name=clean_model,
                        latency_ms=latency,
                        error_code=f"HTTP_{res.status_code}"
                    )
        except Exception as exc:
            return TestConnectionResponse(
                success=False,
                message=self.sanitize_error(exc),
                provider=self.provider_name,
                model_name=clean_model,
                error_code="NETWORK_ERROR"
            )
