from typing import Optional
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.common import APIResponse
from app.schemas.user import UserCreate, UserResponse
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
