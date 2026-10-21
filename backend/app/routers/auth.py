from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db, settings
from app.database.models import User
from app.schemas.common import APIResponse
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    AuthTokenResponse,
    UserAuthResponse,
    ExtensionAuthCodeResponse,
    ExtensionExchangeCodeRequest,
    GoogleAuthRequest,
    AuthConfigResponse,
)
from app.services import auth_service

router = APIRouter(
    prefix="/auth",
    tags=["Authentication & Extension Integration"]
)


def _build_user_auth_response(user: User) -> UserAuthResponse:
    """Helper to format UserAuthResponse with full_name, avatar, and provider."""
    full_name = None
    if user.personal_info and user.personal_info.full_name:
        full_name = user.personal_info.full_name
    elif user.full_name:
        full_name = user.full_name

    avatar_url = user.avatar_url
    if not avatar_url and user.personal_info and user.personal_info.profile_photo:
        avatar_url = user.personal_info.profile_photo

    return UserAuthResponse(
        id=user.id,
        email=user.email,
        full_name=full_name,
        auth_provider=user.auth_provider or "local",
        avatar_url=avatar_url,
        is_active=user.is_active,
        created_at=user.created_at
    )



@router.post(
    "/register",
    response_model=APIResponse[AuthTokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account (Website only)",
    description="Registers a new user on the Magic Fill website using email and password with secure bcrypt hashing."
)
def register_endpoint(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db)
) -> APIResponse[AuthTokenResponse]:
    """Website signup endpoint creating a new user account."""
    user, access_token = auth_service.register_user(
        db=db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name
    )

    return APIResponse(
        success=True,
        message="Registration successful. Welcome to Magic Fill!",
        data=AuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=_build_user_auth_response(user),
            is_new_user=True
        )
    )


@router.post(
    "/login",
    response_model=APIResponse[AuthTokenResponse],
    status_code=status.HTTP_200_OK,
    summary="User sign in (Website only)",
    description="Authenticates an existing user with registered email and password."
)
def login_endpoint(
    payload: UserLoginRequest,
    db: Session = Depends(get_db)
) -> APIResponse[AuthTokenResponse]:
    """Website login endpoint validating user credentials."""
    user, access_token = auth_service.authenticate_user(
        db=db,
        email=payload.email,
        password=payload.password
    )

    return APIResponse(
        success=True,
        message="Login successful",
        data=AuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=_build_user_auth_response(user),
            is_new_user=False
        )
    )


@router.post(
    "/google",
    response_model=APIResponse[AuthTokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate with Google (Continue with Google)",
    description="Verifies a Google ID token server-side, finds or creates the user in PostgreSQL, and establishes an authenticated session."
)
def google_auth_endpoint(
    payload: GoogleAuthRequest,
    db: Session = Depends(get_db)
) -> APIResponse[AuthTokenResponse]:
    """Authenticates or signs up a user using a Google Identity Services ID token."""
    token_str = payload.get_token()
    user, access_token, is_new_user = auth_service.authenticate_or_register_google_user(
        db=db,
        token_str=token_str
    )

    msg = "Welcome to Magic Fill! Account created with Google." if is_new_user else "Welcome back! Signed in with Google."
    return APIResponse(
        success=True,
        message=msg,
        data=AuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=_build_user_auth_response(user),
            is_new_user=is_new_user
        )
    )


@router.get(
    "/config",
    response_model=APIResponse[AuthConfigResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve public auth configuration",
    description="Returns public configuration for Google Identity Services such as the Google Client ID."
)
def auth_config_endpoint() -> APIResponse[AuthConfigResponse]:
    """Returns public authentication parameters for frontend clients."""
    return APIResponse(
        success=True,
        message="Authentication configuration retrieved",
        data=AuthConfigResponse(
            google_client_id=settings.GOOGLE_CLIENT_ID
        )
    )


@router.get(
    "/me",

    response_model=APIResponse[UserAuthResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated user",
    description="Returns the profile and status of the currently authenticated user from Bearer token."
)
def get_me_endpoint(
    current_user: User = Depends(auth_service.get_current_user)
) -> APIResponse[UserAuthResponse]:
    """Returns the authenticated user's account details."""
    return APIResponse(
        success=True,
        message="User profile retrieved",
        data=_build_user_auth_response(current_user)
    )


@router.post(
    "/extension/create-code",
    response_model=APIResponse[ExtensionAuthCodeResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate single-use authorization code for Extension handoff",
    description="Generates a cryptographically random, short-lived (5 min) single-use authorization code bound to the user session."
)
def create_extension_code_endpoint(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[ExtensionAuthCodeResponse]:
    """Generates an authorization code for handing off authentication to the browser extension."""
    auth_code = auth_service.create_extension_auth_code(
        db=db,
        user_id=current_user.id
    )

    return APIResponse(
        success=True,
        message="Extension authorization code generated successfully",
        data=ExtensionAuthCodeResponse(
            code=auth_code.code,
            expires_in_seconds=300
        )
    )


@router.post(
    "/extension/exchange-code",
    response_model=APIResponse[AuthTokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Exchange authorization code for Extension session token",
    description="Browser extension exchanges a single-use authorization code for an authenticated session token. Enforces anti-replay."
)
def exchange_extension_code_endpoint(
    payload: ExtensionExchangeCodeRequest,
    db: Session = Depends(get_db)
) -> APIResponse[AuthTokenResponse]:
    """Exchanges an authorization code for an extension access token."""
    user, access_token = auth_service.exchange_extension_auth_code(
        db=db,
        code=payload.code,
        client_id=payload.client_id or "chrome_extension"
    )

    return APIResponse(
        success=True,
        message="Extension authenticated successfully",
        data=AuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=_build_user_auth_response(user),
            is_new_user=False
        )
    )
