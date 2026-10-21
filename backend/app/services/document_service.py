import re
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.database.models import User, UserDocument, PersonalInfo
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.exceptions import NotFoundException, UserNotFoundException


def classify_document_description(description: str, filename: str = "") -> Tuple[str, str, str]:
    """
    Intelligently classifies a written description into a canonical doc_key, display title, and category.
    Handles user phrases such as:
    - 'this is my cnic front' -> ('cnic_front', 'CNIC Front', 'identity')
    - 'this is my cnic back' -> ('cnic_back', 'CNIC Back', 'identity')
    - 'my profile picture' / 'headshot' -> ('profile_photo', 'Profile Photograph', 'profile')
    - 'my passport scan' -> ('passport', 'Passport Document', 'identity')
    - 'degree transcript' -> ('degree_transcript', 'Degree Transcript', 'academic')
    - 'driving license' -> ('driving_license', 'Driving License', 'identity')
    - 'resume' / 'cv' -> ('resume', 'Resume / CV', 'career')
    """
    text = (description + " " + filename).lower().strip()

    # 1. CNIC Front
    if re.search(r"\b(cnic|id|nic|identity|card)\s*(front|face|first)\b|\bfront\s*(of|side)?\s*(cnic|id|nic|identity)\b", text):
        return ("cnic_front", "CNIC Front", "identity")

    # 2. CNIC Back
    if re.search(r"\b(cnic|id|nic|identity|card)\s*(back|rear|reverse)\b|\bback\s*(of|side)?\s*(cnic|id|nic|identity)\b", text):
        return ("cnic_back", "CNIC Back", "identity")

    # 3. CNIC / National ID (generic)
    if re.search(r"\b(cnic|national\s*id|identity\s*card|id\s*card)\b", text):
        return ("cnic_photo", "CNIC Document", "identity")

    # 4. Profile Photo / Avatar / Headshot
    if re.search(r"\b(profile\s*(photo|picture|pic|image)|headshot|avatar|passport\s*size\s*photo|my\s*photo|my\s*picture)\b", text):
        return ("profile_photo", "Profile Photograph", "profile")

    # 5. Passport
    if re.search(r"\b(passport)\b", text):
        return ("passport", "Passport Document", "identity")

    # 6. Academic / Degree / Transcript
    if re.search(r"\b(degree|transcript|diploma|certificate|graduation)\b", text):
        return ("degree_transcript", "Degree Transcript", "academic")

    # 7. Driving License
    if re.search(r"\b(driving|driver)\s*(licen[sc]e|permit)\b", text):
        return ("driving_license", "Driving License", "identity")

    # 8. Resume / CV
    if re.search(r"\b(resume|cv|curriculum\s*vitae)\b", text):
        return ("resume", "Resume / CV", "career")

    # 9. Fallback slug from description
    cleaned = re.sub(r"[^\w\s]", "", description.lower()).strip()
    words = cleaned.split()
    if words:
        slug = "_".join(words[:4])
        title = " ".join(word.capitalize() for word in words[:4])
    else:
        slug = "document"
        title = "Saved Document"

    return (slug, title, "document")


def save_user_document(db: Session, doc_in: DocumentCreate) -> UserDocument:
    """
    Saves or updates a document with natural language description.
    If a document with the same doc_key already exists for the user, it updates it in place.
    Also synchronizes canonical keys (e.g. cnic_front, profile_photo) to PersonalInfo.
    """
    user = db.query(User).filter(User.id == doc_in.user_id).first()
    if not user:
        raise UserNotFoundException(user_id=doc_in.user_id)

    # Classify if doc_key or title not explicitly provided
    desc = doc_in.description or ""
    auto_key, auto_title, auto_cat = classify_document_description(desc, doc_in.file_name)

    doc_key = doc_in.doc_key or auto_key
    title = doc_in.title or auto_title
    category = doc_in.category or auto_cat

    # Check for existing document with same doc_key
    existing = db.query(UserDocument).filter(
        UserDocument.user_id == doc_in.user_id,
        UserDocument.doc_key == doc_key
    ).first()

    if existing:
        existing.title = title
        existing.description = desc
        existing.file_name = doc_in.file_name
        existing.mime_type = doc_in.mime_type
        existing.file_data = doc_in.file_data
        existing.file_size_bytes = doc_in.file_size_bytes
        existing.category = category
        target_doc = existing
    else:
        new_doc = UserDocument(
            user_id=doc_in.user_id,
            doc_key=doc_key,
            title=title,
            description=desc,
            file_name=doc_in.file_name,
            mime_type=doc_in.mime_type,
            file_data=doc_in.file_data,
            file_size_bytes=doc_in.file_size_bytes,
            category=category
        )
        db.add(new_doc)
        target_doc = new_doc

    # Mirror canonical documents to PersonalInfo (create if not yet existing)
    if not user.personal_info:
        user.personal_info = PersonalInfo(
            user_id=user.id,
            full_name=user.full_name or user.email or "User",
            email=user.email
        )
        db.add(user.personal_info)

    if doc_key in ("profile_photo", "passport_photo", "avatar"):
        user.personal_info.profile_photo = doc_in.file_data
    elif doc_key in ("cnic_front", "cnic_photo", "cnic"):
        user.personal_info.cnic_photo = doc_in.file_data

    # Also mirror as custom field for immediate accessibility across all form matching
    from app.database.models import CustomField
    cf_key = f"doc_{doc_key}"
    existing_cf = db.query(CustomField).filter(
        CustomField.user_id == doc_in.user_id,
        CustomField.field_key == cf_key
    ).first()
    if existing_cf:
        existing_cf.field_value = doc_in.file_data
        existing_cf.field_label = title
    else:
        db.add(CustomField(
            user_id=doc_in.user_id,
            field_key=cf_key,
            field_label=f"{title} (Asset)",
            field_value=doc_in.file_data,
            category=category
        ))

    db.commit()
    db.refresh(target_doc)
    return target_doc


def get_user_documents(db: Session, user_id: int) -> List[UserDocument]:
    """Retrieve all saved documents and photos for a user."""
    return db.query(UserDocument).filter(
        UserDocument.user_id == user_id
    ).order_by(UserDocument.created_at.desc()).all()


def get_document_by_id(db: Session, doc_id: int) -> UserDocument:
    """Retrieve a single document by ID."""
    doc = db.query(UserDocument).filter(UserDocument.id == doc_id).first()
    if not doc:
        raise NotFoundException(message=f"Document with ID {doc_id} not found", error_code="DOCUMENT_NOT_FOUND")
    return doc


def delete_user_document(db: Session, doc_id: int) -> None:
    """Delete a saved document by ID."""
    doc = get_document_by_id(db, doc_id)
    db.delete(doc)
    db.commit()


def update_user_document(db: Session, doc_id: int, doc_update: DocumentUpdate) -> UserDocument:
    """Update title, description, or category of a saved document."""
    doc = get_document_by_id(db, doc_id)
    if doc_update.title is not None:
        doc.title = doc_update.title
    if doc_update.description is not None:
        doc.description = doc_update.description
    if doc_update.category is not None:
        doc.category = doc_update.category

    db.commit()
    db.refresh(doc)
    return doc
