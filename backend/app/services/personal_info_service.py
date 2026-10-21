from sqlalchemy.orm import Session
from app.database.models import PersonalInfo
from app.schemas.personal_info import PersonalInfoCreate, PersonalInfoUpdate
from app.services.user_service import get_user_by_id
from app.exceptions import (
    PersonalInfoNotFoundException,
    PersonalInfoAlreadyExistsException,
)


def create_personal_info(
    db: Session,
    user_id: int,
    info_in: PersonalInfoCreate
) -> PersonalInfo:
    """
    Create a personal information record for the specified user.
    Verifies the user exists and that no existing personal_info record exists for this user.
    """
    # Verify user exists
    get_user_by_id(db, user_id=user_id)

    # Check for existing personal info (enforce 1-to-1)
    existing = db.query(PersonalInfo).filter(PersonalInfo.user_id == user_id).first()
    if existing:
        raise PersonalInfoAlreadyExistsException(user_id=user_id)

    personal_info = PersonalInfo(
        user_id=user_id,
        **info_in.model_dump()
    )
    db.add(personal_info)
    db.commit()
    db.refresh(personal_info)
    return personal_info


def get_personal_info_by_user_id(db: Session, user_id: int) -> PersonalInfo:
    """
    Retrieve personal information for the specified user ID.
    Raises UserNotFoundException if user doesn't exist,
    or PersonalInfoNotFoundException if personal info hasn't been created yet.
    """
    # Verify user exists
    get_user_by_id(db, user_id=user_id)

    personal_info = db.query(PersonalInfo).filter(PersonalInfo.user_id == user_id).first()
    if not personal_info:
        raise PersonalInfoNotFoundException(user_id=user_id)
    return personal_info


def update_personal_info(
    db: Session,
    user_id: int,
    info_in: PersonalInfoUpdate
) -> PersonalInfo:
    """
    Update personal information for the specified user ID.
    Supports partial updates by excluding unset fields.
    """
    # Verify user exists
    get_user_by_id(db, user_id=user_id)

    personal_info = db.query(PersonalInfo).filter(PersonalInfo.user_id == user_id).first()
    if not personal_info:
        raise PersonalInfoNotFoundException(user_id=user_id)

    update_data = info_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(personal_info, field, value)

    db.commit()
    db.refresh(personal_info)
    return personal_info


def delete_personal_info(db: Session, user_id: int) -> None:
    """
    Delete personal information for the specified user ID.
    Raises UserNotFoundException if user doesn't exist,
    or PersonalInfoNotFoundException if personal info hasn't been created yet.
    """
    get_user_by_id(db, user_id=user_id)

    personal_info = db.query(PersonalInfo).filter(PersonalInfo.user_id == user_id).first()
    if not personal_info:
        raise PersonalInfoNotFoundException(user_id=user_id)

    db.delete(personal_info)
    db.commit()
