"""
Magic Fill - AI Configuration & Provider API Endpoints
Provides authenticated endpoints to view, update, test, and reset AI providers.
Ensures API keys are encrypted at rest and never exposed in plaintext.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.provider_manager import (
    AIProviderManager,
    decrypt_api_key,
    encrypt_api_key,
    mask_api_key,
)
from app.ai.response_schema import (
    AIProviderConfig,
    AIProviderConfigPublic,
    AIProviderConfigSaveRequest,
    AIProviderType,
    DEFAULT_MODELS,
    DEFAULT_BASE_URLS,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.database.database import get_db, settings
from app.database.models import User, UserAIConfig
from app.schemas.common import APIResponse
from app.services import auth_service

logger = logging.getLogger("app.routers.ai_config")

router = APIRouter(
    prefix="/ai",
    tags=["AI Provider Configuration"]
)


def _build_public_config(
    provider: str,
    model_name: Optional[str],
    api_base_url: Optional[str],
    has_api_key: bool,
    masked_api_key: Optional[str],
    is_active: bool = True
) -> AIProviderConfigPublic:
    """Constructs a sanitized public view of an AI provider configuration."""
    is_def = provider == AIProviderType.GROQ.value
    resolved_model = model_name or DEFAULT_MODELS.get(provider, "default-model")
    resolved_url = api_base_url or DEFAULT_BASE_URLS.get(provider, "")
    return AIProviderConfigPublic(
        provider=provider,
        model_name=resolved_model,
        api_base_url=resolved_url if resolved_url else None,
        has_api_key=has_api_key,
        masked_api_key=masked_api_key,
        is_default=is_def,
        is_active=is_active,
    )


@router.get(
    "/config",
    response_model=APIResponse[AIProviderConfigPublic],
    summary="Get current user AI provider configuration",
    description="Returns the active AI provider, model, and endpoint settings. API keys are masked."
)
async def get_ai_config(
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[AIProviderConfigPublic]:
    """Retrieves user's AI provider configuration or default Groq configuration."""
    if not current_user:
        # Default unauthenticated public configuration
        public_data = _build_public_config(
            provider=AIProviderType.GROQ.value,
            model_name=DEFAULT_MODELS[AIProviderType.GROQ.value],
            api_base_url=DEFAULT_BASE_URLS[AIProviderType.GROQ.value],
            has_api_key=bool(settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("gsk_your_groq_api_key")),
            masked_api_key=mask_api_key(settings.GROQ_API_KEY),
            is_active=True
        )
        return APIResponse(success=True, message="Default Magic Fill AI configuration", data=public_data)

    config_record = db.query(UserAIConfig).filter(UserAIConfig.user_id == current_user.id).first()
    if not config_record or not config_record.is_active:
        # User has no custom config or inactive; return default Groq
        public_data = _build_public_config(
            provider=AIProviderType.GROQ.value,
            model_name=DEFAULT_MODELS[AIProviderType.GROQ.value],
            api_base_url=DEFAULT_BASE_URLS[AIProviderType.GROQ.value],
            has_api_key=bool(settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("gsk_your_groq_api_key")),
            masked_api_key=mask_api_key(settings.GROQ_API_KEY),
            is_active=True
        )
        return APIResponse(success=True, message="Default Magic Fill AI configuration", data=public_data)

    dec_key = decrypt_api_key(config_record.encrypted_api_key)
    has_key = bool(dec_key) or (config_record.provider == AIProviderType.GROQ.value and bool(settings.GROQ_API_KEY))
    masked = mask_api_key(dec_key) if dec_key else (mask_api_key(settings.GROQ_API_KEY) if config_record.provider == "groq" else None)

    public_data = _build_public_config(
        provider=config_record.provider,
        model_name=config_record.model_name,
        api_base_url=config_record.api_base_url,
        has_api_key=has_key,
        masked_api_key=masked,
        is_active=config_record.is_active
    )
    return APIResponse(success=True, message="User custom AI configuration loaded", data=public_data)


@router.post(
    "/config",
    response_model=APIResponse[AIProviderConfigPublic],
    summary="Save or update custom AI provider configuration",
    description="Encrypts API key and stores user custom LLM preferences."
)
async def save_ai_config(
    payload: AIProviderConfigSaveRequest,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[AIProviderConfigPublic]:
    """Persists user custom AI provider settings with encrypted credentials."""
    target_user_id = current_user.id if current_user else 1

    provider_clean = payload.provider.lower().strip()
    valid_providers = [p.value for p in AIProviderType]
    if provider_clean not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider '{payload.provider}'. Must be one of: {', '.join(valid_providers)}"
        )

    # Resolve model and endpoint defaults
    default_model = DEFAULT_MODELS.get(provider_clean)
    model_to_save = (payload.model_name or "").strip() or default_model
    default_url = DEFAULT_BASE_URLS.get(provider_clean)
    url_to_save = (payload.api_base_url or "").strip() or default_url

    record = db.query(UserAIConfig).filter(UserAIConfig.user_id == target_user_id).first()
    new_encrypted_key = None

    if payload.api_key and payload.api_key.strip():
        # New key provided: encrypt it
        new_encrypted_key = encrypt_api_key(payload.api_key.strip())
    elif record and record.encrypted_api_key and record.provider == provider_clean:
        # Keep existing encrypted key when switching settings within same provider
        new_encrypted_key = record.encrypted_api_key

    if record:
        record.provider = provider_clean
        record.model_name = model_to_save
        record.api_base_url = url_to_save
        if new_encrypted_key is not None:
            record.encrypted_api_key = new_encrypted_key
        record.is_active = payload.is_active
    else:
        record = UserAIConfig(
            user_id=target_user_id,
            provider=provider_clean,
            model_name=model_to_save,
            api_base_url=url_to_save,
            encrypted_api_key=new_encrypted_key,
            is_active=payload.is_active,
        )
        db.add(record)

    db.commit()
    db.refresh(record)

    dec_key = decrypt_api_key(record.encrypted_api_key)
    has_key = bool(dec_key) or (record.provider == AIProviderType.GROQ.value and bool(settings.GROQ_API_KEY))
    masked = mask_api_key(dec_key) if dec_key else (mask_api_key(settings.GROQ_API_KEY) if record.provider == "groq" else None)

    public_data = _build_public_config(
        provider=record.provider,
        model_name=record.model_name,
        api_base_url=record.api_base_url,
        has_api_key=has_key,
        masked_api_key=masked,
        is_active=record.is_active
    )

    return APIResponse(
        success=True,
        message=f"AI Provider successfully configured ({record.provider.title()}: {record.model_name})",
        data=public_data
    )


@router.delete(
    "/config",
    response_model=APIResponse[AIProviderConfigPublic],
    summary="Reset AI provider to default (Groq)",
    description="Removes custom AI configuration and restores standard Magic Fill AI."
)
async def reset_ai_config(
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[AIProviderConfigPublic]:
    """Resets user's AI configuration to default Groq."""
    target_user_id = current_user.id if current_user else 1

    record = db.query(UserAIConfig).filter(UserAIConfig.user_id == target_user_id).first()
    if record:
        db.delete(record)
        db.commit()

    public_data = _build_public_config(
        provider=AIProviderType.GROQ.value,
        model_name=DEFAULT_MODELS[AIProviderType.GROQ.value],
        api_base_url=DEFAULT_BASE_URLS[AIProviderType.GROQ.value],
        has_api_key=bool(settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("gsk_your_groq_api_key")),
        masked_api_key=mask_api_key(settings.GROQ_API_KEY),
        is_active=True
    )
    return APIResponse(
        success=True,
        message="AI Provider configuration reset to default (Groq)",
        data=public_data
    )


@router.post(
    "/test-connection",
    response_model=APIResponse[TestConnectionResponse],
    summary="Test connectivity and model accessibility for an AI provider",
    description="Sends a verification ping to the specified provider and model."
)
async def test_provider_connection_endpoint(
    payload: TestConnectionRequest,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[TestConnectionResponse]:
    """Tests connection to an AI provider without saving or leaking credentials."""
    target_provider = payload.provider.lower().strip()
    target_key = (payload.api_key or "").strip()

    # If key was omitted from request, check if user has a saved key for this provider
    if not target_key and current_user:
        record = db.query(UserAIConfig).filter(
            UserAIConfig.user_id == current_user.id,
            UserAIConfig.provider == target_provider
        ).first()
        if record and record.encrypted_api_key:
            target_key = decrypt_api_key(record.encrypted_api_key) or ""

    resolved_model = (payload.model_name or "").strip() or DEFAULT_MODELS.get(target_provider)
    resolved_base_url = (payload.api_base_url or "").strip() or DEFAULT_BASE_URLS.get(target_provider)

    test_config = AIProviderConfig(
        provider=target_provider,
        model_name=resolved_model,
        api_base_url=resolved_base_url,
        api_key=target_key or (settings.GROQ_API_KEY if target_provider == "groq" else None),
        is_active=True,
    )

    test_result = await AIProviderManager.test_connection(test_config)
    return APIResponse(
        success=test_result.success,
        message=test_result.message,
        data=test_result
    )
