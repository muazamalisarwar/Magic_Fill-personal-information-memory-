from typing import List, Optional
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User
from app.exceptions import AppException
from app.schemas.common import APIResponse
from app.schemas.experience import (
    ExperienceCreate,
    ExperienceUpdate,
    ExperienceResponse,
)
from app.services import experience_service, auth_service

router = APIRouter(
    tags=["Experiences"]
)


def _check_user_access(current_user: Optional[User], requested_user_id: int):
    """Enforces that an authenticated user can only access their own records."""
    if current_user and current_user.id != requested_user_id:
        raise AppException(
            message="Forbidden: You cannot access or modify another user's experiences.",
            error_code="FORBIDDEN",
            status_code=403
        )


@router.get(
    "/experiences/me",
    response_model=APIResponse[List[ExperienceResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user's experiences",
    description="Returns all employment, project, and internship records for the authenticated user."
)
def get_my_experiences_endpoint(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[List[ExperienceResponse]]:
    """Get all experiences for current authenticated user."""
    experiences = experience_service.get_experiences_by_user_id(db=db, user_id=current_user.id)
    return APIResponse(
        success=True,
        message=f"Retrieved {len(experiences)} experiences",
        data=[ExperienceResponse.model_validate(exp) for exp in experiences]
    )


@router.post(
    "/experiences/me",
    response_model=APIResponse[ExperienceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create experience for current user",
    description="Adds a new employment, internship, or project experience record for the authenticated user."
)
def create_my_experience_endpoint(
    experience_in: ExperienceCreate,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[ExperienceResponse]:
    """Create a new work experience for current authenticated user."""
    experience = experience_service.create_experience(
        db=db,
        user_id=current_user.id,
        exp_in=experience_in
    )
    return APIResponse(
        success=True,
        message="Experience created successfully",
        data=ExperienceResponse.model_validate(experience)
    )


@router.post(
    "/users/{user_id}/experiences",
    response_model=APIResponse[ExperienceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create experience for user",
    description="Adds a new employment, internship, or project experience record for the specified user."
)
def create_experience_endpoint(
    experience_in: ExperienceCreate,
    user_id: int = Path(..., gt=0, description="ID of the user", examples=[1]),
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[ExperienceResponse]:
    """Create a new work experience for a user."""
    _check_user_access(current_user, user_id)
    experience = experience_service.create_experience(
        db=db,
        user_id=user_id,
        exp_in=experience_in
    )
    return APIResponse(
        success=True,
        message="Experience created successfully",
        data=ExperienceResponse.model_validate(experience)
    )


@router.get(
    "/users/{user_id}/experiences",
    response_model=APIResponse[List[ExperienceResponse]],
    status_code=status.HTTP_200_OK,
    summary="Retrieve all experiences for user",
    description="Retrieves the chronological list of all experience records associated with the specified user."
)
def get_user_experiences_endpoint(
    user_id: int = Path(..., gt=0, description="ID of the user", examples=[1]),
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[List[ExperienceResponse]]:
    """Retrieve all experiences for a user."""
    _check_user_access(current_user, user_id)
    experiences = experience_service.get_experiences_by_user_id(
        db=db,
        user_id=user_id
    )
    return APIResponse(
        success=True,
        message="Experiences retrieved successfully",
        data=[ExperienceResponse.model_validate(exp) for exp in experiences]
    )


@router.get(
    "/experiences/{experience_id}",
    response_model=APIResponse[ExperienceResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve an individual experience",
    description="Retrieves a specific experience record by its unique experience ID."
)
def get_experience_endpoint(
    experience_id: int = Path(..., gt=0, description="ID of the experience", examples=[1]),
    db: Session = Depends(get_db)
) -> APIResponse[ExperienceResponse]:
    """Retrieve a single experience by ID."""
    experience = experience_service.get_experience_by_id(
        db=db,
        experience_id=experience_id
    )
    return APIResponse(
        success=True,
        message="Experience retrieved successfully",
        data=ExperienceResponse.model_validate(experience)
    )


@router.put(
    "/experiences/{experience_id}",
    response_model=APIResponse[ExperienceResponse],
    status_code=status.HTTP_200_OK,
    summary="Update an individual experience",
    description="Updates fields of an existing experience record by ID. Allows partial updates."
)
@router.post(
    "/experiences/{experience_id}",
    response_model=APIResponse[ExperienceResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
@router.patch(
    "/experiences/{experience_id}",
    response_model=APIResponse[ExperienceResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def update_experience_endpoint(
    experience_in: ExperienceUpdate,
    experience_id: int = Path(..., gt=0, description="ID of the experience", examples=[1]),
    db: Session = Depends(get_db)
) -> APIResponse[ExperienceResponse]:
    """Update an existing experience by ID."""
    experience = experience_service.update_experience(
        db=db,
        experience_id=experience_id,
        exp_in=experience_in
    )
    return APIResponse(
        success=True,
        message="Experience updated successfully",
        data=ExperienceResponse.model_validate(experience)
    )


@router.delete(
    "/experiences/{experience_id}",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete an individual experience",
    description="Deletes a specific experience record by its unique experience ID."
)
def delete_experience_endpoint(
    experience_id: int = Path(..., gt=0, description="ID of the experience to delete", examples=[1]),
    db: Session = Depends(get_db)
) -> APIResponse[None]:
    """Delete an individual experience by ID."""
    experience_service.delete_experience(
        db=db,
        experience_id=experience_id
    )
    return APIResponse(
        success=True,
        message="Experience deleted successfully",
        data=None
    )
