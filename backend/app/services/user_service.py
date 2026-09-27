from typing import Optional
from sqlalchemy.orm import Session
from app.database.models import User
from app.schemas.user import UserCreate
from app.exceptions import UserNotFoundException


def create_user(db: Session, user_in: Optional[UserCreate] = None) -> User:
    """Create a new user in the database."""
    new_user = User()
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_id(db: Session, user_id: int) -> User:
    """
    Retrieve a user by their unique identifier.
    Raises UserNotFoundException if no user matches the ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundException(user_id=user_id)
    return user
