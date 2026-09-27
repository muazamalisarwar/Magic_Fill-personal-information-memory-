from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.orm import relationship
from app.database.database import Base


class User(Base):
    """
    User entity representing a registered individual or identity in the system.
    Supports a 1-to-1 relationship with PersonalInfo and 1-to-N with Experiences.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    personal_info = relationship(
        "PersonalInfo",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    experiences = relationship(
        "Experience",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(Experience.start_date)"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id})>"


class PersonalInfo(Base):
    """
    Personal Information entity (1-to-1 with User).
    Stores personal, contact, and academic details for automated form completion.
    """
    __tablename__ = "personal_info"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Personal details
    full_name = Column(String(150), nullable=False)
    father_name = Column(String(150), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    cnic = Column(String(20), nullable=True, index=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)

    # Address details
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # Academic details
    university = Column(String(200), nullable=True)
    degree = Column(String(150), nullable=True)
    department = Column(String(150), nullable=True)
    semester = Column(String(50), nullable=True)
    registration_number = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationship back to User
    user = relationship("User", back_populates="personal_info")

    def __repr__(self) -> str:
        return f"<PersonalInfo(id={self.id}, user_id={self.user_id}, full_name='{self.full_name}')>"


class Experience(Base):
    """
    Experience entity (1-to-N with User).
    Stores professional work experiences, internships, roles, and acquired skills.
    """
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    company = Column(String(200), nullable=False)
    job_title = Column(String(150), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # Null indicates currently ongoing experience
    description = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)  # Stored as comma-separated or text for universal DB compatibility

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationship back to User
    user = relationship("User", back_populates="experiences")

    def __repr__(self) -> str:
        return f"<Experience(id={self.id}, user_id={self.user_id}, company='{self.company}', job_title='{self.job_title}')>"
