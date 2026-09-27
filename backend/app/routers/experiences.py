from typing import List
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.common import APIResponse
from app.schemas.experience import (
    ExperienceCreate,
    ExperienceUpdate,
    ExperienceResponse,
)
from app.services import experience_service

router = APIRouter(
    tags=["Experiences"]
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
    db: Session = Depends(get_db)
) -> APIResponse[ExperienceResponse]:
    """Create a new work experience for a user."""
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
    db: Session = Depends(get_db)
) -> APIResponse[List[ExperienceResponse]]:
    """Retrieve all experiences for a user."""
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
