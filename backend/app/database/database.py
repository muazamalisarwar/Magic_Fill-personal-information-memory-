import os
from typing import Generator, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session


class Settings(BaseSettings):
    """Application and database settings loaded from environment variables."""
    APP_NAME: str = "Personal Information Memory API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DATABASE_URL: str = "postgresql+psycopg://magic_fill_user:575092@localhost:5432/magic_fill"

    # JWT Security Configuration
    SECRET_KEY: str = "magic_fill_production_jwt_secret_key_secure_2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Groq LLM Configuration for intelligent extraction & semantic matching
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # Google OAuth 2.0 Web Client Configuration
    GOOGLE_CLIENT_ID: Optional[str] = "456121937465-pog6ha9pfgl8cjru833rer0o74j44tbe.apps.googleusercontent.com"

    # Support locating .env in backend directory or current working directory
    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
            ".env"
        ),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# PostgreSQL production connection pool configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.DEBUG and settings.APP_ENV == "development"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy database session per request
    and ensures proper closing on completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
