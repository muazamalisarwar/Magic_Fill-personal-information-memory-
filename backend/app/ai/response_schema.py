"""
Magic Fill - AI Provider Schemas & Data Models
Defines configuration schemas, provider types, and test connection payloads.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AIProviderType(str, Enum):
    """Supported AI Providers in Magic Fill."""
    GROQ = "groq"
    OPENAI = "openai"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    CUSTOM = "custom"


# Sensible default models per provider
DEFAULT_MODELS: Dict[str, str] = {
    AIProviderType.GROQ.value: "openai/gpt-oss-20b",
    AIProviderType.OPENAI.value: "gpt-4o-mini",
    AIProviderType.GEMINI.value: "gemini-1.5-flash",
    AIProviderType.OPENROUTER.value: "meta-llama/llama-3.3-70b-instruct",
    AIProviderType.OLLAMA.value: "llama3.2",
    AIProviderType.CUSTOM.value: "gpt-3.5-turbo",
}

# Default API endpoints per provider
DEFAULT_BASE_URLS: Dict[str, str] = {
    AIProviderType.GROQ.value: "https://api.groq.com/openai/v1",
    AIProviderType.OPENAI.value: "https://api.openai.com/v1",
    AIProviderType.GEMINI.value: "https://generativelanguage.googleapis.com/v1beta",
    AIProviderType.OPENROUTER.value: "https://openrouter.ai/api/v1",
    AIProviderType.OLLAMA.value: "http://localhost:11434/v1",
    AIProviderType.CUSTOM.value: "",
}


class AIProviderConfig(BaseModel):
    """Internal schema for AI provider configuration."""
    provider: str = Field(default="groq", description="Provider identifier (groq, openai, gemini, openrouter, ollama, custom)")
    model_name: Optional[str] = Field(default=None, description="Configured LLM model identifier")
    api_base_url: Optional[str] = Field(default=None, description="Custom API endpoint base URL")
    api_key: Optional[str] = Field(default=None, description="Plaintext API key (only in memory, never logged)")
    is_active: bool = Field(default=True, description="Whether this configuration is currently active")

    model_config = ConfigDict(extra="ignore")


class AIProviderConfigSaveRequest(BaseModel):
    """Request payload sent by client to update user AI configuration."""
    provider: str = Field(..., description="Provider identifier")
    model_name: Optional[str] = Field(None, description="Selected model name")
    api_base_url: Optional[str] = Field(None, description="Custom API base URL")
    api_key: Optional[str] = Field(None, description="New API key to encrypt and save (or null to keep existing)")
    is_active: bool = Field(default=True, description="Whether custom config is active")

    model_config = ConfigDict(extra="ignore")


class AIProviderConfigPublic(BaseModel):
    """Sanitized public view of user's AI configuration (never exposes raw API keys)."""
    provider: str = Field(..., description="Active provider identifier")
    model_name: str = Field(..., description="Active model name")
    api_base_url: Optional[str] = Field(None, description="Configured API base URL")
    has_api_key: bool = Field(..., description="True if a valid API key is currently saved")
    masked_api_key: Optional[str] = Field(None, description="Masked preview of the key (e.g. 'sk-...4a2b')")
    is_default: bool = Field(..., description="True if using default Magic Fill Groq AI")
    is_active: bool = Field(..., description="Whether custom config is active")

    model_config = ConfigDict(from_attributes=True)


class TestConnectionRequest(BaseModel):
    """Request payload to test connectivity with an AI provider."""
    provider: str = Field(..., description="Provider identifier to test")
    model_name: Optional[str] = Field(None, description="Model to test")
    api_base_url: Optional[str] = Field(None, description="Custom API base URL to test")
    api_key: Optional[str] = Field(None, description="API key to test (optional if already saved)")

    model_config = ConfigDict(extra="ignore")


class TestConnectionResponse(BaseModel):
    """Response returned after running a provider connection test."""
    success: bool = Field(..., description="Whether connection and test completion succeeded")
    message: str = Field(..., description="Human-friendly message describing status or error")
    provider: str = Field(..., description="Provider tested")
    model_name: Optional[str] = Field(None, description="Model tested")
    latency_ms: Optional[float] = Field(None, description="Round-trip latency in milliseconds")
    error_code: Optional[str] = Field(None, description="Error classification if failed")
    installed_models: Optional[List[str]] = Field(None, description="List of installed models (for Ollama)")

    model_config = ConfigDict(extra="ignore")
