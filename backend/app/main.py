import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database.database import Base, engine, settings
from app.exceptions import AppException
from app.routers import (
    users_router,
    personal_info_router,
    experiences_router,
)
from app.schemas.common import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes database tables on startup.
    """
    logger.info("Initializing relational database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as exc:
        logger.error("Failed to initialize database tables: %s", str(exc))
    yield
    logger.info("Application shutdown complete.")


# OpenAPI tags metadata
openapi_tags = [
    {
        "name": "System",
        "description": "System health and status monitoring endpoints."
    },
    {
        "name": "Users",
        "description": "User identity operations. A user can have one personal information profile and multiple experiences."
    },
    {
        "name": "Personal Information",
        "description": "Personal, academic, and contact information management (1-to-1 relationship with User)."
    },
    {
        "name": "Experiences",
        "description": "Professional, internship, and project experience management (1-to-N relationship with User)."
    }
]

app = FastAPI(
    title="Personal Information Memory API",
    description=(
        "Backend API for Personal Information Memory & Intelligent Form Completion. "
        "Provides RESTful endpoints for managing personal profiles, academic background, "
        "and multi-role professional experiences with full relational persistence."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Enable CORS for frontend, Postman, and future browser extension integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Global Exception Handlers (Clean and secure, never expose raw DB credentials)
# -----------------------------------------------------------------------------

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handles domain-level application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
            **({"details": exc.details} if exc.details is not None else {})
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles Pydantic validation errors and formats them into the standard error schema."""
    formatted_errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        formatted_errors.append({
            "field": field,
            "message": err.get("msg"),
            "type": err.get("type")
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "success": False,
            "message": "Validation error in request body or parameters",
            "error_code": "VALIDATION_ERROR",
            "details": formatted_errors
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handles standard HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
            "error_code": f"HTTP_{exc.status_code}"
        }
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Safely captures database errors without leaking internal connection strings,
    passwords, or internal database table definitions.
    """
    logger.error("Database error occurred: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "A database error occurred while processing the request",
            "error_code": "DATABASE_ERROR"
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captures unhandled exceptions and returns a sanitized 500 error."""
    logger.exception("Unhandled server error: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected server error occurred",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )


# -----------------------------------------------------------------------------
# System Endpoints
# -----------------------------------------------------------------------------

@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Health check",
    description="Returns backend running and health status."
)
def health_check() -> dict:
    """Health check endpoint confirming that backend is running."""
    return {
        "success": True,
        "message": "Backend is running",
        "status": "healthy"
    }


# -----------------------------------------------------------------------------
# Routers Registration
# -----------------------------------------------------------------------------
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(personal_info_router, prefix=settings.API_V1_PREFIX)
app.include_router(experiences_router, prefix=settings.API_V1_PREFIX)
