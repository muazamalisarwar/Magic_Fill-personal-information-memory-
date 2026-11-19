"""
Magic Fill - BYO-LLM Unit Test Suite
Tests all AI providers, Provider Manager, Key Encryption, and AI Config Endpoints.
"""

import pytest
from unittest.mock import patch, AsyncMock
from app.ai.response_schema import (
    AIProviderConfig,
    AIProviderType,
    DEFAULT_MODELS,
    DEFAULT_BASE_URLS,
)
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


def test_encryption_and_masking():
    """Verify AES/Fernet encryption, decryption, and key masking."""
    secret = "sk-1234567890abcdef"
    encrypted = encrypt_api_key(secret)
    assert encrypted != secret
    assert len(encrypted) > 20

    decrypted = decrypt_api_key(encrypted)
    assert decrypted == secret

    # Empty / None handling
    assert encrypt_api_key(None) is None
    assert encrypt_api_key("") is None
    assert decrypt_api_key(None) is None
    assert decrypt_api_key("invalid-token") is None

    # Masking
    masked = mask_api_key("sk-abcdefgh12345678")
    assert masked.startswith("sk-a...")
    assert masked.endswith("5678")
    assert "cdefgh" not in masked


def test_base_provider_clean_and_parse_json():
    """Test JSON cleaning across various LLM formatting quirks."""
    # 1. Plain clean JSON
    res = BaseAIProvider.clean_and_parse_json('{"key": "value"}')
    assert res == {"key": "value"}

    # 2. Markdown fenced code block
    res_fenced = BaseAIProvider.clean_and_parse_json('```json\n{"status": "ok", "count": 42}\n```')
    assert res_fenced == {"status": "ok", "count": 42}

    # 3. Conversational prefix and suffix
    res_convo = BaseAIProvider.clean_and_parse_json('Here is the parsed output:\n\n{"mappings": []}\n\nHope this helps!')
    assert res_convo == {"mappings": []}

    # 4. Trailing commas
    res_comma = BaseAIProvider.clean_and_parse_json('{"name": "Muazam", "skills": ["python", "fastapi",],}')
    assert res_comma["name"] == "Muazam"


def test_provider_manager_factory():
    """Verify ProviderManager instantiates correct classes per provider type."""
    assert isinstance(AIProviderManager.get_provider_instance(AIProviderConfig(provider="groq")), GroqProvider)
    assert isinstance(AIProviderManager.get_provider_instance(AIProviderConfig(provider="openai")), OpenAIProvider)
    assert isinstance(AIProviderManager.get_provider_instance(AIProviderConfig(provider="gemini")), GeminiProvider)
    assert isinstance(AIProviderManager.get_provider_instance(AIProviderConfig(provider="openrouter")), OpenRouterProvider)
    assert isinstance(AIProviderManager.get_provider_instance(AIProviderConfig(provider="ollama")), OllamaProvider)
    assert isinstance(AIProviderManager.get_provider_instance(AIProviderConfig(provider="custom")), OpenAICompatibleProvider)
    # Default fallback
    assert isinstance(AIProviderManager.get_provider_instance(AIProviderConfig(provider="unknown_xyz")), GroqProvider)


@pytest.mark.anyio
async def test_openai_provider_mock():
    """Verify OpenAIProvider chat completion and test connection with mocked HTTP."""
    from unittest.mock import MagicMock
    cfg = AIProviderConfig(provider="openai", api_key="sk-test-mock-key", model_name="gpt-4o-mini")
    provider = OpenAIProvider(cfg)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"mappings": [{"field_id": "name", "value": "Muazam Ali"}]}'}}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        res = await provider.chat_completion([{"role": "user", "content": "hi"}])
        assert res is not None
        assert "mappings" in res
        assert res["mappings"][0]["value"] == "Muazam Ali"

        test_res = await provider.test_connection()
        assert test_res.success is True
        assert "Connected successfully" in test_res.message


@pytest.mark.anyio
async def test_gemini_provider_mock():
    """Verify GeminiProvider chat completion and test connection with mocked HTTP."""
    from unittest.mock import MagicMock
    cfg = AIProviderConfig(provider="gemini", api_key="AIzaSy-mock-key", model_name="gemini-1.5-flash")
    provider = GeminiProvider(cfg)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {"parts": [{"text": '{"mappings": [{"field_id": "email", "value": "test@example.com"}]}'}]}
        }]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        res = await provider.chat_completion([{"role": "user", "content": "extract"}])
        assert res is not None
        assert res["mappings"][0]["value"] == "test@example.com"

        test_res = await provider.test_connection()
        assert test_res.success is True


@pytest.mark.anyio
async def test_ollama_provider_mock():
    """Verify OllamaProvider handling of installed models and connection test."""
    from unittest.mock import MagicMock
    cfg = AIProviderConfig(provider="ollama", model_name="llama3.2", api_base_url="http://localhost:11434/v1")
    provider = OllamaProvider(cfg)

    # 1. Mock tags response showing llama3.2 is installed
    mock_tags_res = MagicMock()
    mock_tags_res.status_code = 200
    mock_tags_res.json.return_value = {"models": [{"name": "llama3.2:latest"}, {"name": "mistral:latest"}]}

    # 2. Mock completion response
    mock_comp_res = MagicMock()
    mock_comp_res.status_code = 200
    mock_comp_res.json.return_value = {
        "choices": [{"message": {"content": '{"status": "ok"}'}}]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_tags_res
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_comp_res
            installed = await provider.list_installed_models()
            assert "llama3.2:latest" in installed

            test_res = await provider.test_connection()
            assert test_res.success is True
            assert "Connected successfully to local Ollama" in test_res.message


def test_ai_config_api_endpoints(client):
    """Test GET /api/ai/config, POST /api/ai/config, DELETE /api/ai/config."""
    # 1. Create a user
    user_res = client.post("/api/users", json={}).json()
    user_id = user_res["data"]["id"]

    # 2. Default config should be Groq
    get_res = client.get("/api/ai/config")
    assert get_res.status_code == 200
    data = get_res.json()["data"]
    assert data["provider"] == "groq"
    assert data["is_default"] is True

    # 3. Save custom OpenAI config
    save_res = client.post(
        "/api/ai/config",
        json={
            "provider": "openai",
            "model_name": "gpt-4o-mini",
            "api_key": "sk-realtestkey123456789",
            "is_active": True
        }
    )
    assert save_res.status_code == 200
    saved_data = save_res.json()["data"]
    assert saved_data["provider"] == "openai"
    assert saved_data["model_name"] == "gpt-4o-mini"
    assert saved_data["has_api_key"] is True
    # Ensure key is masked and not plaintext
    assert "sk-realtestkey123456789" not in save_res.text
    assert saved_data["masked_api_key"].startswith("sk-r...")

    # 4. Save Ollama config
    ollama_res = client.post(
        "/api/ai/config",
        json={
            "provider": "ollama",
            "model_name": "llama3.2",
            "api_base_url": "http://localhost:11434/v1",
            "is_active": True
        }
    )
    assert ollama_res.status_code == 200
    assert ollama_res.json()["data"]["provider"] == "ollama"

    # 5. Reset to default
    del_res = client.delete("/api/ai/config")
    assert del_res.status_code == 200
    assert del_res.json()["data"]["provider"] == "groq"
    assert del_res.json()["data"]["is_default"] is True
