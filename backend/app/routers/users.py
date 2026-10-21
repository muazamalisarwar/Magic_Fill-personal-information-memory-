from typing import Optional
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.common import APIResponse
from app.schemas.user import UserCreate, UserResponse, UserProfileResponse
from app.schemas.personal_info import PersonalInfoResponse
from app.schemas.custom_field import CustomFieldResponse
from app.schemas.experience import ExperienceResponse
from app.schemas.document import DocumentResponse
from app.services import user_service

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)



@router.post(
    "",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Registers a new user identity in the system to hold personal information and work experiences."
)
def create_user_endpoint(
    user_in: Optional[UserCreate] = None,
    db: Session = Depends(get_db)
) -> APIResponse[UserResponse]:
    """Create a new user."""
    user = user_service.create_user(db=db, user_in=user_in)
    return APIResponse(
        success=True,
        message="User created successfully",
        data=UserResponse.model_validate(user)
    )


@router.get(
    "/{user_id}",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve user details",
    description="Retrieves the user record with timestamps by user ID."
)
def get_user_endpoint(
    user_id: int = Path(..., gt=0, description="ID of the user to retrieve", examples=[1]),
    db: Session = Depends(get_db)
) -> APIResponse[UserResponse]:
    """Retrieve a user by ID."""
    user = user_service.get_user_by_id(db=db, user_id=user_id)
    return APIResponse(
        success=True,
        message="User retrieved successfully",
        data=UserResponse.model_validate(user)
    )


@router.delete(
    "/{user_id}",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete user",
    description="Deletes a user identity and cascades deletion to associated personal information and experiences."
)
def delete_user_endpoint(
    user_id: int = Path(..., gt=0, description="ID of the user to delete", examples=[1]),
    db: Session = Depends(get_db)
) -> APIResponse[None]:
    """Delete a user by ID."""
    user_service.delete_user(db=db, user_id=user_id)
    return APIResponse(
        success=True,
        message="User deleted successfully",
        data=None
    )


from app.database.models import User
from app.exceptions import AppException
from app.services import user_service, auth_service

@router.get(
    "/{user_id}/profile",
    response_model=APIResponse[UserProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve full user profile",
    description="Retrieves the unified user profile including identity, personal info, and experiences for autofill."
)
def get_user_profile_endpoint(
    user_id: int = Path(..., gt=0, description="ID of the user", examples=[1]),
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[UserProfileResponse]:
    """Retrieve full aggregated profile for a user."""
    if current_user and current_user.id != user_id:
        raise AppException(
            message="Forbidden: You cannot access another user's profile.",
            error_code="FORBIDDEN",
            status_code=403
        )
    profile_data = user_service.get_user_profile(db=db, user_id=user_id)
    return APIResponse(
        success=True,
        message="User profile retrieved successfully",
        data=UserProfileResponse(
            user=UserResponse.model_validate(profile_data["user"]),
            personal_info=PersonalInfoResponse.model_validate(profile_data["personal_info"]) if profile_data["personal_info"] else None,
            experiences=[ExperienceResponse.model_validate(exp) for exp in profile_data["experiences"]],
            custom_fields=[CustomFieldResponse.model_validate(cf) for cf in profile_data.get("custom_fields", [])],
            documents=[DocumentResponse.model_validate(d) for d in profile_data.get("documents", [])]
        )
    )

