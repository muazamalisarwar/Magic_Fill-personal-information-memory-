from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.common import APIResponse
from app.schemas.matching import FieldMatchRequest, FieldMatchResponse
from app.services.matching_service import match_form_fields
from app.database.models import User
from app.services import auth_service
from app.exceptions import AppException

router = APIRouter(
    prefix="/matching",
    tags=["Form Matching"]
)


@router.post(
    "/fields",
    response_model=APIResponse[FieldMatchResponse],
    status_code=status.HTTP_200_OK,
    summary="Match detected website form fields to personal memory",
    description=(
        "Analyzes a list of detected form input fields from an active webpage and maps them "
        "to the specified user's stored personal, academic, and professional memory. "
        "Utilizes fast deterministic matching for common fields and falls back to the Groq LLM "
        "for ambiguous or non-standard semantic field labels."
    )
)
async def match_fields_endpoint(
    request: FieldMatchRequest,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[FieldMatchResponse]:
    """Matches webpage form fields to user personal memory."""
    if current_user:
        request.user_id = current_user.id
    elif not request.user_id:
        raise AppException(
            message="User identification required. Please provide user_id or Authorization header.",
            error_code="UNAUTHORIZED",
            status_code=401
        )
    match_result = await match_form_fields(db=db, request=request)
    return APIResponse(
        success=True,
        message=f"Successfully processed {match_result.total_detected} fields ({match_result.total_mapped} mapped)",
        data=match_result
    )
