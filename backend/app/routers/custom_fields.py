from typing import List
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.common import APIResponse
from app.schemas.custom_field import (
    CustomFieldCreate,
    CustomFieldUpdate,
    CustomFieldResponse,
)
from app.database.models import User, CustomField
from app.exceptions import AppException
from app.services import custom_field_service, auth_service

router = APIRouter(
    tags=["Custom Memory Fields"]
)


@router.get(
    "/custom-fields/me",
    response_model=APIResponse[List[CustomFieldResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all custom fields for current authenticated user",
    description="Retrieves dynamic attributes, learned Q&As, and custom memory fields for the authenticated user."
)
@router.get(
    "/custom-fields/me/",
    response_model=APIResponse[List[CustomFieldResponse]],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
@router.get(
    "/custom-fields",
    response_model=APIResponse[List[CustomFieldResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all custom fields for current authenticated user (alias)",
    include_in_schema=False
)
@router.get(
    "/custom-fields/",
    response_model=APIResponse[List[CustomFieldResponse]],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def list_my_custom_fields_endpoint(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[List[CustomFieldResponse]]:
    """Retrieve all custom fields for current authenticated user."""
    fields = custom_field_service.get_custom_fields_by_user(db=db, user_id=current_user.id)
    return APIResponse(
        success=True,
        message=f"Retrieved {len(fields)} custom fields",
        data=[CustomFieldResponse.model_validate(f) for f in fields]
    )


@router.post(
    "/custom-fields/me",
    response_model=APIResponse[CustomFieldResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom memory field for current authenticated user",
    description="Adds a new dynamic attribute or learned Q&A to the authenticated user's memory."
)
@router.post(
    "/custom-fields/me/",
    response_model=APIResponse[CustomFieldResponse],
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
)
@router.post(
    "/custom-fields",
    response_model=APIResponse[CustomFieldResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom memory field for current authenticated user (alias)",
    include_in_schema=False
)
@router.post(
    "/custom-fields/",
    response_model=APIResponse[CustomFieldResponse],
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
)
def create_my_custom_field_endpoint(
    field_in: CustomFieldCreate,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[CustomFieldResponse]:
    """Create a new custom field for current authenticated user."""
    created = custom_field_service.create_custom_field(db=db, user_id=current_user.id, field_in=field_in)
    return APIResponse(
        success=True,
        message="Custom field created successfully",
        data=CustomFieldResponse.model_validate(created)
    )


@router.get(
    "/users/{user_id}/custom-fields",
    response_model=APIResponse[List[CustomFieldResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all custom fields for a user",
    description="Retrieves dynamic attributes, contacts, and custom memory fields associated with the user."
)
def list_custom_fields_endpoint(
    user_id: int = Path(..., gt=0, description="ID of the user", examples=[1]),
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[List[CustomFieldResponse]]:
    """Retrieve all custom fields for a user."""
    target_user_id = current_user.id if current_user else user_id
    fields = custom_field_service.get_custom_fields_by_user(db=db, user_id=target_user_id)
    return APIResponse(
        success=True,
        message=f"Retrieved {len(fields)} custom fields",
        data=[CustomFieldResponse.model_validate(f) for f in fields]
    )


@router.post(
    "/users/{user_id}/custom-fields",
    response_model=APIResponse[CustomFieldResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom memory field for a user",
    description="Adds a new dynamic attribute (e.g. friend's name, emergency contact, passport number) to user memory."
)
def create_custom_field_endpoint(
    user_id: int = Path(..., gt=0, description="ID of the user", examples=[1]),
    field_in: CustomFieldCreate = ...,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[CustomFieldResponse]:
    """Create a new custom field for a user."""
    target_user_id = current_user.id if current_user else user_id
    created = custom_field_service.create_custom_field(db=db, user_id=target_user_id, field_in=field_in)
    return APIResponse(
        success=True,
        message="Custom field created successfully",
        data=CustomFieldResponse.model_validate(created)
    )


@router.put(
    "/custom-fields/{field_id}",
    response_model=APIResponse[CustomFieldResponse],
    status_code=status.HTTP_200_OK,
    summary="Update a custom memory field",
    description="Modifies an existing custom attribute's label, value, or category."
)
@router.post(
    "/custom-fields/{field_id}",
    response_model=APIResponse[CustomFieldResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
@router.patch(
    "/custom-fields/{field_id}",
    response_model=APIResponse[CustomFieldResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def update_custom_field_endpoint(
    field_id: int = Path(..., gt=0, description="ID of the custom field", examples=[1]),
    field_in: CustomFieldUpdate = ...,
    db: Session = Depends(get_db)
) -> APIResponse[CustomFieldResponse]:
    """Update a custom field."""
    updated = custom_field_service.update_custom_field(db=db, field_id=field_id, field_in=field_in)
    return APIResponse(
        success=True,
        message="Custom field updated successfully",
        data=CustomFieldResponse.model_validate(updated)
    )


@router.delete(
    "/custom-fields/{field_id}",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a custom memory field",
    description="Permanently deletes a custom memory field."
)
def delete_custom_field_endpoint(
    field_id: int = Path(..., gt=0, description="ID of the custom field to delete", examples=[1]),
    db: Session = Depends(get_db)
) -> APIResponse[None]:
    """Delete a custom field."""
    custom_field_service.delete_custom_field(db=db, field_id=field_id)
    return APIResponse(
        success=True,
        message="Custom field deleted successfully",
        data=None
    )
