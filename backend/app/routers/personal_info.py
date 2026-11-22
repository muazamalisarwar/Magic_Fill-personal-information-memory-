from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.common import APIResponse
from app.schemas.personal_info import (
    PersonalInfoCreate,
    PersonalInfoUpdate,
    PersonalInfoResponse,
)
from typing import Optional
from app.database.models import User
from app.exceptions import AppException
from app.services import personal_info_service, auth_service

router = APIRouter(
    tags=["Personal Information"]
)


def _check_user_access(current_user: Optional[User], requested_user_id: int):
    """Enforces that an authenticated user can only access their own records."""
    if current_user and current_user.id != requested_user_id:
        raise AppException(
            message="Forbidden: You cannot access or modify another user's personal information.",
            error_code="FORBIDDEN",
            status_code=403
        )


@router.get(
    "/personal-info/me",
    response_model=APIResponse[Optional[PersonalInfoResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user's personal information",
    description="Returns the personal, academic, and contact information for the authenticated user."
)
def get_my_personal_info_endpoint(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[Optional[PersonalInfoResponse]]:
    """Get personal information for current authenticated user."""
    info = personal_info_service.get_personal_info_by_user_id(db=db, user_id=current_user.id)
    return APIResponse(
        success=True,
        message="Personal information retrieved successfully",
        data=PersonalInfoResponse.model_validate(info) if info else None
    )


@router.put(
    "/personal-info/me",
    response_model=APIResponse[PersonalInfoResponse],
    status_code=status.HTTP_200_OK,
    summary="Update current authenticated user's personal information",
    description="Updates or creates personal, academic, and contact information for the authenticated user."
)
@router.post(
    "/personal-info/me",
    response_model=APIResponse[PersonalInfoResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
@router.patch(
    "/personal-info/me",
    response_model=APIResponse[PersonalInfoResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def update_my_personal_info_endpoint(
    personal_info_in: PersonalInfoUpdate,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[PersonalInfoResponse]:
    """Update personal information for current authenticated user."""
    info = personal_info_service.get_personal_info_by_user_id(db=db, user_id=current_user.id)
    if not info:
        info = personal_info_service.create_personal_info(
            db=db,
            user_id=current_user.id,
            info_in=PersonalInfoCreate(**personal_info_in.model_dump(exclude_unset=True))
        )
    else:
        info = personal_info_service.update_personal_info(
            db=db,
            user_id=current_user.id,
            info_in=personal_info_in
        )
    return APIResponse(
        success=True,
        message="Personal information updated successfully",
        data=PersonalInfoResponse.model_validate(info)
    )


@router.delete(
    "/personal-info/me/fields/{field_name}",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Clear an individual personal info field",
    description="Clears or deletes a single specific field from the authenticated user's personal information profile."
)
def clear_my_personal_info_field_endpoint(
    field_name: str = Path(..., description="Name of the field to clear (e.g. phone, address, university)"),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[None]:
    """Clears a specific field on the authenticated user's personal info record."""
    info = personal_info_service.get_personal_info_by_user_id(db=db, user_id=current_user.id)
    if not info:
        raise AppException(message="Personal info record not found", error_code="NOT_FOUND", status_code=404)

    if hasattr(info, field_name):
        setattr(info, field_name, None)
        if field_name == "full_name":
            user = db.query(User).filter(User.id == current_user.id).first()
            if user:
                user.full_name = ""
        db.commit()
        db.refresh(info)
    else:
        raise AppException(message=f"Field '{field_name}' not found on personal info", error_code="INVALID_FIELD", status_code=400)

    return APIResponse(
        success=True,
        message=f"Field '{field_name}' cleared successfully",
        data=None
    )


@router.delete(
    "/users/{user_id}/personal-info/fields/{field_name}",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Clear an individual personal info field by user ID",
    description="Clears or deletes a single specific field from the specified user's personal information profile."
)
def clear_user_personal_info_field_endpoint(
    user_id: int = Path(..., gt=0, description="ID of the user"),
    field_name: str = Path(..., description="Name of the field to clear"),
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[None]:
    """Clears a specific field on the user's personal info record."""
    _check_user_access(current_user, user_id)
    info = personal_info_service.get_personal_info_by_user_id(db=db, user_id=user_id)
    if not info:
        raise AppException(message="Personal info record not found", error_code="NOT_FOUND", status_code=404)

    if hasattr(info, field_name):
        setattr(info, field_name, None)
        if field_name == "full_name":
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.full_name = ""
        db.commit()
    else:
        raise AppException(message=f"Field '{field_name}' not found on personal info", error_code="INVALID_FIELD", status_code=400)

    return APIResponse(
        success=True,
        message=f"Field '{field_name}' cleared successfully",
        data=None
    )


@router.post(
    "/users/{user_id}/personal-info",
    response_model=APIResponse[PersonalInfoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create personal information for user",
    description="Stores personal, academic, and contact information for the specified user."
)
def create_personal_info_endpoint(
    personal_info_in: PersonalInfoCreate,
    user_id: int = Path(..., gt=0, description="ID of the user", examples=[1]),
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[PersonalInfoResponse]:
    """Create personal information for a user."""
    _check_user_access(current_user, user_id)
    info = personal_info_service.create_personal_info(
        db=db,
        user_id=user_id,
        info_in=personal_info_in
    )
    return APIResponse(
        success=True,
        message="Personal information created successfully",
        data=PersonalInfoResponse.model_validate(info)
    )


@router.get(
    "/users/{user_id}/personal-info",
    response_model=APIResponse[PersonalInfoResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve personal information for user",
    description="Fetches the personal, academic, and contact information recorded for the specified user."
)
def get_personal_info_endpoint(
    user_id: int = Path(..., gt=0, description="ID of the user", examples=[1]),
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[PersonalInfoResponse]:
    """Retrieve personal information for a user."""
    _check_user_access(current_user, user_id)
    info = personal_info_service.get_personal_info_by_user_id(
        db=db,
        user_id=user_id
    )
    return APIResponse(
        success=True,
        message="Personal information retrieved successfully",
        data=PersonalInfoResponse.model_validate(info)
    )


@router.put(
    "/users/{user_id}/personal-info",
    response_model=APIResponse[PersonalInfoResponse],
    status_code=status.HTTP_200_OK,
    summary="Update personal information for user",
    description="Updates existing personal information for the specified user. Allows partial updates."
)
def update_personal_info_endpoint(
    personal_info_in: PersonalInfoUpdate,
    user_id: int = Path(..., gt=0, description="ID of the user", examples=[1]),
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[PersonalInfoResponse]:
    """Update personal information for a user."""
    _check_user_access(current_user, user_id)
    info = personal_info_service.update_personal_info(
        db=db,
        user_id=user_id,
        info_in=personal_info_in
    )
    return APIResponse(
        success=True,
        message="Personal information updated successfully",
        data=PersonalInfoResponse.model_validate(info)
    )


@router.delete(
    "/users/{user_id}/personal-info",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete personal information for user",
    description="Deletes personal, academic, and contact information for the specified user."
)
def delete_personal_info_endpoint(
    user_id: int = Path(..., gt=0, description="ID of the user", examples=[1]),
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[None]:
    """Delete personal information for a user."""
    _check_user_access(current_user, user_id)
    personal_info_service.delete_personal_info(
        db=db,
        user_id=user_id
    )
    return APIResponse(
        success=True,
        message="Personal information deleted successfully",
        data=None
    )
