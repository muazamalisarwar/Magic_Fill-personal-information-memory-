import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.database import settings, get_db
from app.database.models import User, PersonalInfo, AuthCode
from app.exceptions import (
    AuthenticationException,
    DuplicateEmailException,
    InvalidAuthCodeException,
    UserNotFoundException,
)
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests


security_scheme = HTTPBearer(auto_error=False)


def hash_password(plain_password: str) -> str:
    """Hashes a plaintext password using bcrypt with random salt (safe up to 72 bytes)."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8")[:72], salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Encodes a payload into a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a signed JWT token."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def register_user(
    db: Session,
    email: str,
    password: str,
    full_name: Optional[str] = None
) -> Tuple[User, str]:
    """
    Registers a new user on the Magic Fill website.
    Validates email uniqueness, securely hashes password, creates account,
    initializes personal memory profile, and returns (user, access_token).
    """
    normalized_email = email.strip().lower()
    cleaned_full_name = full_name.strip() if full_name and full_name.strip() else None

    existing_user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if existing_user:
        raise DuplicateEmailException(email=normalized_email)

    new_user = User(
        email=normalized_email,
        hashed_password=hash_password(password),
        full_name=cleaned_full_name,
        auth_provider="local",
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initialize personal_info profile unconditionally so user has a profile ready
    personal_info = PersonalInfo(
        user_id=new_user.id,
        full_name=cleaned_full_name or "",
        email=normalized_email
    )
    db.add(personal_info)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})
    return new_user, access_token


def authenticate_user(
    db: Session,
    email: str,
    password: str
) -> Tuple[User, str]:
    """
    Authenticates an existing user using email and password.
    Returns (user, access_token) upon successful verification.
    """
    normalized_email = email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()

    if not user:
        raise AuthenticationException(
            message="Invalid email or password. Please verify your credentials.",
            error_code="INVALID_CREDENTIALS"
        )

    if user.auth_provider == "google" and not user.hashed_password:
        raise AuthenticationException(
            message="This account was registered with Google. Please click 'Continue with Google' to sign in.",
            error_code="USE_GOOGLE_SIGN_IN"
        )

    if not user.hashed_password or not verify_password(password, user.hashed_password):
        raise AuthenticationException(
            message="Invalid email or password. Please verify your credentials.",
            error_code="INVALID_CREDENTIALS"
        )

    if not user.is_active:
        raise AuthenticationException(
            message="This account has been deactivated. Please contact support.",
            error_code="ACCOUNT_DEACTIVATED"
        )

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return user, access_token


def create_extension_auth_code(
    db: Session,
    user_id: int,
    client_id: str = "chrome_extension"
) -> AuthCode:
    """
    Generates a cryptographically random, short-lived single-use authorization code
    for secure website-to-extension authentication handoff.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundException(user_id=user_id)

    # Invalidate any previously unused codes for this user to minimize exposure window
    db.query(AuthCode).filter(AuthCode.user_id == user_id, AuthCode.used.is_(False)).update({"used": True})

    # Generate user-friendly 8-character uppercase code (e.g. MF-7A9B3E2F)
    code_alphabet = string.ascii_uppercase + string.digits
    random_part = "".join(secrets.choice(code_alphabet) for _ in range(8))
    code_str = f"MF-{random_part}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)  # 5-minute validity window

    auth_code = AuthCode(
        code=code_str,
        user_id=user_id,
        expires_at=expires_at,
        used=False,
        client_id=client_id
    )
    db.add(auth_code)
    db.commit()
    db.refresh(auth_code)
    return auth_code


def exchange_extension_auth_code(
    db: Session,
    code: str,
    client_id: str = "chrome_extension"
) -> Tuple[User, str]:
    """
    Validates and consumes a single-use authorization code, returning an extension
    JWT access token. Enforces single-use anti-replay and expiration checks.
    """
    normalized_code = (code or "").strip().upper()
    auth_code = db.query(AuthCode).filter(func.upper(AuthCode.code) == normalized_code).first()

    if not auth_code:
        raise InvalidAuthCodeException("Authorization code is invalid or does not exist.")

    if auth_code.used:
        raise InvalidAuthCodeException("Authorization code has already been used.")

    now = datetime.now(timezone.utc)
    # Ensure timezone awareness for comparison
    expires_at = auth_code.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        raise InvalidAuthCodeException("Authorization code has expired. Please sign in again.")

    # Mark as consumed immediately to prevent replay
    auth_code.used = True
    db.commit()

    user = db.query(User).filter(User.id == auth_code.user_id).first()
    if not user or not user.is_active:
        raise AuthenticationException("Associated user account is no longer active.")

    # Issue an authenticated session token for the extension
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "client": client_id},
        expires_delta=timedelta(days=14)  # 14 days for extension convenience
    )
    return user, token


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that validates the Bearer token in the Authorization header
    and retrieves the corresponding active User entity.
    """
    if not credentials or not credentials.credentials:
        raise AuthenticationException(
            message="Authentication required. Please sign in to access this resource.",
            error_code="UNAUTHORIZED"
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload or "sub" not in payload:
        raise AuthenticationException(
            message="Invalid, tampered, or expired session token. Please sign in again.",
            error_code="INVALID_TOKEN"
        )

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise AuthenticationException(
            message="Invalid token claims.",
            error_code="INVALID_TOKEN"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise AuthenticationException(
            message="User associated with this token was not found or is deactivated.",
            error_code="USER_NOT_FOUND"
        )

    return user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    FastAPI dependency for endpoints that can optionally be authenticated.
    Returns the User if valid credentials are provided, or None otherwise.
    """
    if not credentials or not credentials.credentials:
        return None

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None

    try:
        user_id = int(payload["sub"])
        user = db.query(User).filter(User.id == user_id).first()
        return user if user and user.is_active else None
    except Exception:
        return None


def verify_google_id_token(token_str: str) -> Dict[str, Any]:
    """
    Verifies a Google ID token server-side using Google Identity Services public keys.
    Validates token signature, audience, issuer, expiration, and essential claims.
    """
    if not token_str or not token_str.strip():
        raise AuthenticationException(
            message="Google credential token is missing or empty.",
            error_code="INVALID_GOOGLE_TOKEN"
        )

    client_id = settings.GOOGLE_CLIENT_ID
    if not client_id:
        raise AuthenticationException(
            message="Google OAuth Client ID is not configured on the server.",
            error_code="OAUTH_CONFIG_ERROR"
        )

    # Allow simulated token in local development for testing when localhost origin is unverified by Google Console
    if getattr(settings, "APP_ENV", "development") == "development" and token_str.startswith("dev-token-google:"):
        parts = token_str.split(":", 2)
        demo_email = parts[1] if len(parts) > 1 and parts[1] else "google.demo@magicfill.ai"
        demo_name = parts[2] if len(parts) > 2 and parts[2] else "Google Demo User"
        return {
            "iss": "https://accounts.google.com",
            "sub": f"google-dev-sub-{abs(hash(demo_email)) % 100000000}",
            "email": demo_email,
            "email_verified": True,
            "name": demo_name,
            "picture": "https://lh3.googleusercontent.com/a/default-user=s96-c"
        }

    try:
        # Verify the ID token with Google's public certificates
        request = google_requests.Request()
        id_info = google_id_token.verify_oauth2_token(
            token_str.strip(),
            request,
            audience=client_id,
            clock_skew_in_seconds=10
        )
    except ValueError as exc:
        raise AuthenticationException(
            message=f"Google ID token verification failed: {str(exc)}",
            error_code="INVALID_GOOGLE_TOKEN"
        )
    except Exception as exc:
        raise AuthenticationException(
            message=f"Google authentication service error: {str(exc)}",
            error_code="GOOGLE_AUTH_ERROR"
        )

    # Validate issuer
    issuer = id_info.get("iss")
    if issuer not in ("accounts.google.com", "https://accounts.google.com"):
        raise AuthenticationException(
            message=f"Invalid Google token issuer: {issuer}",
            error_code="INVALID_TOKEN_ISSUER"
        )

    # Validate subject identifier
    sub = id_info.get("sub")
    if not sub:
        raise AuthenticationException(
            message="Google token missing subject identifier (sub).",
            error_code="INVALID_GOOGLE_TOKEN"
        )

    # Validate email
    email = id_info.get("email")
    if not email:
        raise AuthenticationException(
            message="Google token missing email claim.",
            error_code="INVALID_GOOGLE_TOKEN"
        )

    return id_info


def authenticate_or_register_google_user(
    db: Session,
    token_str: str
) -> Tuple[User, str, bool]:
    """
    Verifies the Google ID token and finds or creates the corresponding User in PostgreSQL.
    Enforces safe account linking, unique identity constraints, and database persistence.
    Returns (user, access_token, is_new_user).
    """
    payload = verify_google_id_token(token_str)

    google_sub = str(payload["sub"]).strip()
    email = str(payload.get("email", "")).strip().lower()
    email_verified = bool(payload.get("email_verified", False))
    name = payload.get("name")
    picture = payload.get("picture")

    # 1. First, search by unique google_id (repeat Google login)
    existing_user_by_google = db.query(User).filter(User.google_id == google_sub).first()
    if existing_user_by_google:
        if not existing_user_by_google.is_active:
            raise AuthenticationException(
                message="This account has been deactivated. Please contact support.",
                error_code="ACCOUNT_DEACTIVATED"
            )

        # Update profile avatar or name if not already set or changed
        changed = False
        if picture and existing_user_by_google.avatar_url != picture:
            existing_user_by_google.avatar_url = picture
            changed = True
        if name and not existing_user_by_google.full_name:
            existing_user_by_google.full_name = name
            changed = True
        if changed:
            db.commit()
            db.refresh(existing_user_by_google)

        access_token = create_access_token(
            data={"sub": str(existing_user_by_google.id), "email": existing_user_by_google.email}
        )
        return existing_user_by_google, access_token, False

    # 2. Check if an account already exists with this verified email
    existing_user_by_email = db.query(User).filter(User.email == email).first()
    if existing_user_by_email:
        if not existing_user_by_email.is_active:
            raise AuthenticationException(
                message="This account has been deactivated. Please contact support.",
                error_code="ACCOUNT_DEACTIVATED"
            )

        # Safe account linking: Only link if Google confirms email ownership
        if not email_verified:
            raise AuthenticationException(
                message="Cannot link Google account because the email address is not verified by Google.",
                error_code="UNVERIFIED_EMAIL"
            )

        # Link google_id to the existing user record
        existing_user_by_email.google_id = google_sub
        if picture and not existing_user_by_email.avatar_url:
            existing_user_by_email.avatar_url = picture
        if name and not existing_user_by_email.full_name:
            existing_user_by_email.full_name = name
        db.commit()
        db.refresh(existing_user_by_email)

        access_token = create_access_token(
            data={"sub": str(existing_user_by_email.id), "email": existing_user_by_email.email}
        )
        return existing_user_by_email, access_token, False

    # 3. New user signup via Google - Persist in PostgreSQL
    new_user = User(
        email=email,
        google_id=google_sub,
        auth_provider="google",
        avatar_url=picture,
        full_name=name,
        hashed_password=None,  # No password stored for Google accounts
        is_active=True
    )
    db.add(new_user)
    db.flush()  # Populates new_user.id within transaction

    # Automatically initialize personal_info profile for grounding & autofill
    display_name = name.strip() if name and name.strip() else email.split("@")[0].capitalize()
    personal_info = PersonalInfo(
        user_id=new_user.id,
        full_name=display_name,
        email=email,
        profile_photo=picture
    )
    db.add(personal_info)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email}
    )
    return new_user, access_token, True

