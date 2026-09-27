from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.common import APIResponse
from app.schemas.personal_info import (
    PersonalInfoCreate,
    PersonalInfoUpdate,
    PersonalInfoResponse,
)
from app.services import personal_info_service

router = APIRouter(
    tags=["Personal Information"]
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
    db: Session = Depends(get_db)
) -> APIResponse[PersonalInfoResponse]:
    """Create personal information for a user."""
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
    db: Session = Depends(get_db)
) -> APIResponse[PersonalInfoResponse]:
    """Retrieve personal information for a user."""
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
    db: Session = Depends(get_db)
) -> APIResponse[PersonalInfoResponse]:
    """Update personal information for a user."""
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
