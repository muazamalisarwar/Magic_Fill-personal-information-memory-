from typing import List
from sqlalchemy.orm import Session
from app.database.models import Experience
from app.schemas.experience import ExperienceCreate, ExperienceUpdate
from app.services.user_service import get_user_by_id
from app.exceptions import ExperienceNotFoundException, BadRequestException


def create_experience(
    db: Session,
    user_id: int,
    exp_in: ExperienceCreate
) -> Experience:
    """
    Create a new experience entry for the specified user.
    Verifies that the user exists.
    """
    get_user_by_id(db, user_id=user_id)

    experience = Experience(
        user_id=user_id,
        **exp_in.model_dump()
    )
    db.add(experience)
    db.commit()
    db.refresh(experience)
    return experience


def get_experiences_by_user_id(
    db: Session,
    user_id: int
) -> List[Experience]:
    """
    Retrieve all experience entries for a user, ordered with newest roles first.
    Verifies that the user exists.
    """
    get_user_by_id(db, user_id=user_id)

    experiences = (
        db.query(Experience)
        .filter(Experience.user_id == user_id)
        .order_by(Experience.start_date.desc())
        .all()
    )
    return experiences


def get_experience_by_id(
    db: Session,
    experience_id: int
) -> Experience:
    """
    Retrieve a single experience entry by its unique ID.
    Raises ExperienceNotFoundException if not found.
    """
    experience = db.query(Experience).filter(Experience.id == experience_id).first()
    if not experience:
        raise ExperienceNotFoundException(experience_id=experience_id)
    return experience


def update_experience(
    db: Session,
    experience_id: int,
    exp_in: ExperienceUpdate
) -> Experience:
    """
    Update an existing experience entry.
    Validates cross-field date consistency if dates are updated.
    """
    experience = get_experience_by_id(db, experience_id=experience_id)

    update_data = exp_in.model_dump(exclude_unset=True)

    # Cross-validate effective start and end dates
    effective_start = update_data.get("start_date", experience.start_date)
    effective_end = update_data.get("end_date", experience.end_date)
    if effective_start and effective_end and effective_end < effective_start:
        raise BadRequestException(
            message="end_date cannot be earlier than start_date",
            error_code="INVALID_DATE_RANGE"
        )

    for field, value in update_data.items():
        setattr(experience, field, value)

    db.commit()
    db.refresh(experience)
    return experience
