"""
Magic Fill - Ollama (Local LLM) Provider
Connects to a locally running Ollama instance with zero cloud dependencies.
Enables 100% private and sovereign form autofill and profile processing.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx
from app.ai.base_provider import BaseAIProvider
from app.ai.prompts import TEST_CONNECTION_PROMPT
from app.ai.response_schema import AIProviderConfig, TestConnectionResponse, DEFAULT_MODELS, DEFAULT_BASE_URLS

logger = logging.getLogger("app.ai.ollama_provider")


class OllamaProvider(BaseAIProvider):
    """
    Ollama Local LLM Provider implementation.
    Communicates with local Ollama daemon via OpenAI-compatible endpoints
    (http://localhost:11434/v1) and native inspection endpoints.
    """

    def __init__(self, config: Optional[AIProviderConfig] = None):
        cfg = config or AIProviderConfig(provider="ollama")
        super().__init__(cfg)
        self.api_base_url = self.api_base_url or DEFAULT_BASE_URLS["ollama"]
        self.endpoint_url = f"{self.api_base_url}/chat/completions"
        self.model_name = self.model_name or DEFAULT_MODELS["ollama"]
        # Root host without '/v1' for native Ollama API endpoints like /api/tags
        self.root_host = self.api_base_url.replace("/v1", "").rstrip("/")

    async def list_installed_models(self) -> List[str]:
        """Queries Ollama native /api/tags endpoint to return list of installed model names."""
        try:
            url = f"{self.root_host}/api/tags"
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                    return models
        except Exception:
            pass
        return []

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        timeout_seconds: float = 45.0,  # Local LLMs can take slightly longer depending on hardware
        response_json: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Sends chat completion to local Ollama instance with structured JSON output."""
        current_model = model or self.model_name
        headers = {"Content-Type": "application/json"}
        payload: Dict[str, Any] = {
            "model": current_model,
            "messages": messages,
            "temperature": temperature,
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
                    logger.warning("Ollama error HTTP %d: %s", res.status_code, res.text[:120])
                    return None
        except httpx.ConnectError:
            logger.warning("Could not connect to Ollama at %s. Ensure 'ollama serve' is running.", self.endpoint_url)
            return None
        except Exception as exc:
            logger.warning("Ollama execution error: %s", self.sanitize_error(exc))
            return None

    async def test_connection(self) -> TestConnectionResponse:
        """Verifies if Ollama is running, checks installed models, and runs test completion."""
        start_time = time.time()

        # Step 1: Ping /api/tags to see if Ollama is running and inspect models
        installed_models = await self.list_installed_models()
        if not installed_models:
            # Check basic root reachability
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    ping_res = await client.get(self.root_host)
                    if ping_res.status_code != 200:
                        return TestConnectionResponse(
                            success=False,
                            message=f"Connection refused at {self.root_host}. Ensure Ollama is installed and running (`ollama serve`).",
                            provider=self.provider_name,
                            model_name=self.model_name,
                            error_code="CONNECTION_REFUSED"
                        )
            except Exception:
                return TestConnectionResponse(
                    success=False,
                    message=f"Could not connect to Ollama at {self.root_host}. Make sure Ollama is running (`ollama serve`) on your computer.",
                    provider=self.provider_name,
                    model_name=self.model_name,
                    error_code="CONNECTION_REFUSED"
                )

        # Step 2: Check if requested model is in installed models
        clean_target = self.model_name.lower().split(":")[0]
        model_found = any(clean_target in m.lower() for m in installed_models)
        if not model_found and installed_models:
            models_display = ", ".join(installed_models[:5])
            return TestConnectionResponse(
                success=False,
                message=(
                    f"Model '{self.model_name}' is not installed in Ollama.\n"
                    f"Installed models: {models_display}.\n"
                    f"Run `ollama pull {self.model_name}` in your terminal to install it."
                ),
                provider=self.provider_name,
                model_name=self.model_name,
                installed_models=installed_models,
                error_code="MODEL_NOT_INSTALLED"
            )

        # Step 3: Run quick test completion
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": TEST_CONNECTION_PROMPT}],
            "response_format": {"type": "json_object"},
            "max_tokens": 50,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(self.endpoint_url, json=payload, headers={"Content-Type": "application/json"})
                latency = round((time.time() - start_time) * 1000, 1)

                if res.status_code == 200:
                    return TestConnectionResponse(
                        success=True,
                        message=f"Connected successfully to local Ollama ({self.model_name}) in {latency}ms!",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency,
                        installed_models=installed_models
                    )
                else:
                    return TestConnectionResponse(
                        success=False,
                        message=f"Ollama returned HTTP {res.status_code}: {res.text[:120]}",
                        provider=self.provider_name,
                        model_name=self.model_name,
                        latency_ms=latency,
                        installed_models=installed_models,
                        error_code=f"HTTP_{res.status_code}"
                    )
        except httpx.ConnectError:
            return TestConnectionResponse(
                success=False,
                message=f"Connection refused at {self.endpoint_url}. Verify that Ollama is running (`ollama serve`).",
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
