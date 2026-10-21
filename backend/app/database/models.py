from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    Boolean,
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
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    auth_provider = Column(String(50), default="local", nullable=False)
    avatar_url = Column(String(1024), nullable=True)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
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
    custom_fields = relationship(
        "CustomField",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="asc(CustomField.id)"
    )
    documents = relationship(
        "UserDocument",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(UserDocument.created_at)"
    )
    auth_codes = relationship(
        "AuthCode",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"


class AuthCode(Base):
    """
    Short-lived, single-use authorization code for secure website-to-extension handoff.
    Binds an authenticated web session to the browser extension without exposing passwords.
    """
    __tablename__ = "auth_codes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    client_id = Column(String(100), nullable=True, default="chrome_extension")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    user = relationship("User", back_populates="auth_codes")

    def __repr__(self) -> str:
        return f"<AuthCode(id={self.id}, user_id={self.user_id}, used={self.used})>"


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
    gender = Column(String(30), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    cnic = Column(String(20), nullable=True, index=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)

    # Document & Image details
    profile_photo = Column(Text, nullable=True)  # Base64 data URI or image URL
    cnic_photo = Column(Text, nullable=True)     # Base64 data URI or document URL

    # Address details
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)


    # Academic details
    university = Column(String(200), nullable=True)
    degree = Column(String(150), nullable=True)
    major = Column(String(150), nullable=True)
    department = Column(String(150), nullable=True)
    semester = Column(String(50), nullable=True)
    registration_number = Column(String(100), nullable=True)
    graduation_year = Column(String(50), nullable=True)

    # Professional & Online presence
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)

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


class CustomField(Base):
    """
    Custom dynamic field or extended memory attribute (1-to-N with User).
    Stores user-defined attributes, contacts, references, extra emails, emergency info, etc.
    """
    __tablename__ = "custom_fields"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    field_key = Column(String(100), nullable=False, index=True)
    field_label = Column(String(150), nullable=False)
    field_value = Column(Text, nullable=False)
    category = Column(String(50), nullable=True, default="general")

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
    user = relationship("User", back_populates="custom_fields")

    def __repr__(self) -> str:
        return f"<CustomField(id={self.id}, user_id={self.user_id}, key='{self.field_key}', val='{self.field_value}')>"


class UserDocument(Base):
    """
    User Document / Media entity (1-to-N with User).
    Stores photos, identification cards (CNIC Front, CNIC Back, Passport),
    credentials, and certificates with written natural language descriptions.
    """
    __tablename__ = "user_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    doc_key = Column(String(100), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_data = Column(Text, nullable=False)  # Base64 data URI
    file_size_bytes = Column(Integer, nullable=True)
    category = Column(String(50), nullable=True, default="identity")

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
    user = relationship("User", back_populates="documents")

    def __repr__(self) -> str:
        return f"<UserDocument(id={self.id}, user_id={self.user_id}, doc_key='{self.doc_key}', title='{self.title}')>"


