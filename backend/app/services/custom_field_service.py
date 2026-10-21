import re
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.models import CustomField, User
from app.schemas.custom_field import CustomFieldCreate, CustomFieldUpdate
from app.exceptions import CustomFieldNotFoundException, UserNotFoundException


def _normalize_key(key: str) -> str:
    """Normalize field key for consistent matching."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", key.strip().lower())
    return cleaned.strip("_")


def get_custom_fields_by_user(db: Session, user_id: int) -> List[CustomField]:
    """Retrieve all custom dynamic fields for a specific user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundException(user_id=user_id)
    return db.query(CustomField).filter(CustomField.user_id == user_id).order_by(CustomField.id.asc()).all()


def get_custom_field_by_id(db: Session, field_id: int) -> CustomField:
    """Retrieve a single custom field by its ID."""
    field = db.query(CustomField).filter(CustomField.id == field_id).first()
    if not field:
        raise CustomFieldNotFoundException(field_id=field_id)
    return field


def create_custom_field(db: Session, user_id: int, field_in: CustomFieldCreate) -> CustomField:
    """Create a new custom field for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundException(user_id=user_id)

    new_field = CustomField(
        user_id=user_id,
        field_key=_normalize_key(field_in.field_key),
        field_label=field_in.field_label.strip(),
        field_value=field_in.field_value.strip(),
        category=field_in.category or "general"
    )
    db.add(new_field)
    db.commit()
    db.refresh(new_field)
    return new_field


def update_custom_field(db: Session, field_id: int, field_in: CustomFieldUpdate) -> CustomField:
    """Update an existing custom field."""
    field = get_custom_field_by_id(db, field_id=field_id)
    update_data = field_in.model_dump(exclude_unset=True)

    if "field_label" in update_data and update_data["field_label"] is not None:
        field.field_label = update_data["field_label"].strip()
    if "field_value" in update_data and update_data["field_value"] is not None:
        field.field_value = update_data["field_value"].strip()
    if "category" in update_data and update_data["category"] is not None:
        field.category = update_data["category"].strip()

    db.commit()
    db.refresh(field)
    return field


def delete_custom_field(db: Session, field_id: int) -> None:
    """Delete a custom field."""
    field = get_custom_field_by_id(db, field_id=field_id)
    db.delete(field)
    db.commit()


def upsert_custom_field_by_key(
    db: Session,
    user_id: int,
    field_key: str,
    field_label: str,
    field_value: str,
    category: Optional[str] = None
) -> CustomField:
    """
    Intelligently inserts a new custom field or updates an existing one if the key or label matches.
    Prevents duplicate entries when user adds or updates information multiple times.
    """
    norm_key = _normalize_key(field_key)
    norm_label = re.sub(r"[^a-zA-Z0-9]+", " ", field_label.strip().lower()).strip()

    existing_fields = db.query(CustomField).filter(CustomField.user_id == user_id).all()

    matched_field: Optional[CustomField] = None
    for f in existing_fields:
        f_norm_key = _normalize_key(f.field_key)
        f_norm_label = re.sub(r"[^a-zA-Z0-9]+", " ", f.field_label.strip().lower()).strip()
        if f_norm_key == norm_key or f_norm_label == norm_label:
            matched_field = f
            break

    if matched_field:
        # Update existing field value
        matched_field.field_value = field_value.strip()
        matched_field.field_label = field_label.strip()
        if category:
            matched_field.category = category
        db.commit()
        db.refresh(matched_field)
        return matched_field

    # Create new field
    new_field = CustomField(
        user_id=user_id,
        field_key=norm_key,
        field_label=field_label.strip(),
        field_value=field_value.strip(),
        category=category or "general"
    )
    db.add(new_field)
    db.commit()
    db.refresh(new_field)
    return new_field
