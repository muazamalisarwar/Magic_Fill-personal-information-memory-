import base64
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.common import APIResponse
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate
from app.services.document_service import (
    save_user_document,
    get_user_documents,
    get_document_by_id,
    delete_user_document,
    update_user_document,
)

from app.database.models import User
from app.services import auth_service

router = APIRouter(
    prefix="/documents",
    tags=["Documents & Media Management"]
)


@router.post(
    "",
    response_model=APIResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Save document or photo with written description (JSON Data URI)",
    description="Saves a photo, CNIC front/back, or document along with a natural language description. Automatically classifies document type and mirrors canonical keys."
)
def create_document_json(
    payload: DocumentCreate,
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[DocumentResponse]:
    """Saves a document or photo provided as Base64 data URI."""
    if current_user:
        payload.user_id = current_user.id
    doc = save_user_document(db=db, doc_in=payload)
    return APIResponse(
        success=True,
        message=f"Document '{doc.title}' saved successfully to personal vault",
        data=DocumentResponse.model_validate(doc)
    )


@router.post(
    "/upload",
    response_model=APIResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload image or document file with written description (Multipart)",
    description="Accepts a file upload (image/PDF/doc) alongside a description (e.g., 'this is my cnic front'). Converts to Data URI and classifies."
)
async def upload_document_multipart(
    file: UploadFile = File(...),
    description: str = Form(..., description="What this document or photo is (e.g. 'this is my cnic front')"),
    user_id: int = Form(default=1),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[DocumentResponse]:
    """Uploads a file and stores it with its written description."""
    target_user_id = current_user.id if current_user else user_id
    content_bytes = await file.read()
    mime = file.content_type or "application/octet-stream"
    b64_content = base64.b64encode(content_bytes).decode("utf-8")
    data_uri = f"data:{mime};base64,{b64_content}"

    doc_in = DocumentCreate(
        user_id=target_user_id,
        file_name=file.filename or "upload.bin",
        mime_type=mime,
        file_data=data_uri,
        file_size_bytes=len(content_bytes),
        description=description,
        title=title,
        category=category or "identity"
    )

    doc = save_user_document(db=db, doc_in=doc_in)
    return APIResponse(
        success=True,
        message=f"Uploaded and stored '{doc.title}' in personal memory",
        data=DocumentResponse.model_validate(doc)
    )


@router.get(
    "",
    response_model=APIResponse[List[DocumentResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all documents and photos for user"
)
def list_documents(
    user_id: int = Query(default=1, gt=0),
    current_user: Optional[User] = Depends(auth_service.get_optional_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[List[DocumentResponse]]:
    """Lists all saved documents for the given user."""
    target_user_id = current_user.id if current_user else user_id
    docs = get_user_documents(db=db, user_id=target_user_id)
    return APIResponse(
        success=True,
        message=f"Retrieved {len(docs)} documents",
        data=[DocumentResponse.model_validate(d) for d in docs]
    )


@router.get(
    "/me",
    response_model=APIResponse[List[DocumentResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all documents and photos for current authenticated user"
)
def list_my_documents(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse[List[DocumentResponse]]:
    """Lists all saved documents for current authenticated user."""
    docs = get_user_documents(db=db, user_id=current_user.id)
    return APIResponse(
        success=True,
        message=f"Retrieved {len(docs)} documents",
        data=[DocumentResponse.model_validate(d) for d in docs]
    )


@router.get(
    "/{doc_id}",
    response_model=APIResponse[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get single document by ID"
)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db)
) -> APIResponse[DocumentResponse]:
    """Fetches a single document by its ID."""
    doc = get_document_by_id(db=db, doc_id=doc_id)
    return APIResponse(
        success=True,
        message="Document retrieved successfully",
        data=DocumentResponse.model_validate(doc)
    )


@router.put(
    "/{doc_id}",
    response_model=APIResponse[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="Update document title, description, or category"
)
def update_document(
    doc_id: int,
    payload: DocumentUpdate,
    db: Session = Depends(get_db)
) -> APIResponse[DocumentResponse]:
    """Updates document metadata."""
    doc = update_user_document(db=db, doc_id=doc_id, doc_update=payload)
    return APIResponse(
        success=True,
        message="Document updated successfully",
        data=DocumentResponse.model_validate(doc)
    )


@router.delete(
    "/me/{doc_id}",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
@router.delete(
    "/{doc_id}",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete document from vault"
)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db)
) -> APIResponse[None]:
    """Deletes a document from the vault."""
    delete_user_document(db=db, doc_id=doc_id)
    return APIResponse(
        success=True,
        message="Document deleted successfully",
        data=None
    )
