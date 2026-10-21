from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserRegisterRequest(BaseModel):
    """Payload for user registration on the website."""
    email: EmailStr = Field(..., description="Valid unique user email address")
    password: str = Field(..., min_length=6, max_length=128, description="User password (min 6 characters)")
    full_name: Optional[str] = Field(None, max_length=150, description="Optional user full name")

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class UserLoginRequest(BaseModel):
    """Payload for user login on the website."""
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="User password")

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class UserAuthResponse(BaseModel):
    """User profile data returned upon successful authentication."""
    id: int = Field(..., description="Unique user identifier")
    email: Optional[str] = Field(None, description="Registered email address")
    full_name: Optional[str] = Field(None, description="Full name from personal info if available")
    auth_provider: str = Field("local", description="Authentication provider: local or google")
    avatar_url: Optional[str] = Field(None, description="Profile avatar URL if available")
    is_active: bool = Field(True, description="Account active status")
    created_at: datetime = Field(..., description="Timestamp of account creation")

    model_config = ConfigDict(from_attributes=True)


class GoogleAuthRequest(BaseModel):
    """Payload containing Google ID token from Google Identity Services."""
    credential: Optional[str] = Field(None, description="Google ID Token issued by Google Identity Services")
    id_token: Optional[str] = Field(None, description="Alternative field name for Google ID token")

    @model_validator(mode="after")
    def check_token_present(self) -> "GoogleAuthRequest":
        tok = (self.credential or self.id_token or "").strip()
        if not tok:
            raise ValueError("Google ID token (credential or id_token) is required.")
        return self

    def get_token(self) -> str:
        return (self.credential or self.id_token or "").strip()



class AuthConfigResponse(BaseModel):
    """Public authentication configuration returned to the frontend."""
    google_client_id: Optional[str] = Field(None, description="Configured Google OAuth Client ID")



class AuthTokenResponse(BaseModel):
    """JWT Bearer token and user context returned on registration and login."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    user: UserAuthResponse = Field(..., description="Authenticated user details")
    is_new_user: bool = Field(False, description="Whether the user just completed new registration")

    model_config = ConfigDict(from_attributes=True)


class ExtensionAuthCodeResponse(BaseModel):
    """Single-use authorization code for secure website-to-extension handoff."""
    code: str = Field(..., description="Short-lived single-use authorization code")
    expires_in_seconds: int = Field(300, description="Lifetime of authorization code (5 minutes)")

    model_config = ConfigDict(from_attributes=True)


class ExtensionExchangeCodeRequest(BaseModel):
    """Payload sent by browser extension to exchange an authorization code for an authenticated session."""
    code: str = Field(..., min_length=6, max_length=128, description="Single-use authorization code")
    client_id: Optional[str] = Field("chrome_extension", description="Client identifier")

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
