import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database.database import Base, engine, settings
from app.exceptions import AppException
from app.routers import (
    users_router,
    personal_info_router,
    experiences_router,
    matching_router,
    memory_router,
    custom_fields_router,
    documents_router,
    auth_router,
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
    Initializes PostgreSQL database tables on startup and validates connectivity.
    """
    logger.info("Initializing relational database tables on PostgreSQL...")
    try:
        Base.metadata.create_all(bind=engine)
        # Ensure auth columns exist on existing users table in PostgreSQL
        if engine.dialect.name == "postgresql":
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255)"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255)"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255)"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(50) DEFAULT 'local'"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(1024)"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255)"))
                # Ensure extended personal info columns exist
                conn.execute(text("ALTER TABLE personal_info ADD COLUMN IF NOT EXISTS major VARCHAR(150)"))
                conn.execute(text("ALTER TABLE personal_info ADD COLUMN IF NOT EXISTS graduation_year VARCHAR(50)"))
                conn.execute(text("ALTER TABLE personal_info ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(500)"))
                conn.execute(text("ALTER TABLE personal_info ADD COLUMN IF NOT EXISTS github_url VARCHAR(500)"))
                conn.execute(text("ALTER TABLE personal_info ADD COLUMN IF NOT EXISTS bio TEXT"))
                conn.commit()

        logger.info("Database tables and auth schema initialized successfully on PostgreSQL.")
    except Exception as exc:
        logger.error("Failed to initialize database tables: %s", str(exc))
        raise exc
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
    },
    {
        "name": "Form Matching",
        "description": "Intelligent form-field detection and semantic memory mapping for browser autofill."
    },
    {
        "name": "Documents & Media Management",
        "description": "Upload, categorize, and store photos, CNIC front/back, and credentials with written descriptions."
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
@app.get(
    "/api/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Health check (API prefix)",
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
# Routers Registration (Mount auth_router at /api/auth and /auth for compatibility)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix="")

app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(personal_info_router, prefix=settings.API_V1_PREFIX)
app.include_router(experiences_router, prefix=settings.API_V1_PREFIX)
app.include_router(matching_router, prefix=settings.API_V1_PREFIX)
app.include_router(memory_router, prefix=settings.API_V1_PREFIX)
app.include_router(custom_fields_router, prefix=settings.API_V1_PREFIX)
app.include_router(documents_router, prefix=settings.API_V1_PREFIX)


# -----------------------------------------------------------------------------
# Static Web Dashboard & Automark Template Website Mounting
# -----------------------------------------------------------------------------
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

backend_dir = os.path.dirname(os.path.dirname(__file__))
project_root = os.path.dirname(backend_dir)
web_dir = os.path.join(backend_dir, "web")
automark_dist = os.path.join(project_root, "automark-v1.0.0", "dist")

os.makedirs(web_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=web_dir), name="static")

# Mount Automark static bundles if built
if os.path.exists(automark_dist):
    astro_dir = os.path.join(automark_dist, "_astro")
    if os.path.exists(astro_dir):
        app.mount("/_astro", StaticFiles(directory=astro_dir), name="astro_assets")

    images_dir = os.path.join(automark_dist, "images")
    if os.path.exists(images_dir):
        app.mount("/images", StaticFiles(directory=images_dir), name="automark_images")

    scripts_dir = os.path.join(automark_dist, "scripts")
    if os.path.exists(scripts_dir):
        app.mount("/scripts", StaticFiles(directory=scripts_dir), name="automark_scripts")


@app.get("/showcase.mp4", include_in_schema=False)
def serve_showcase_video():
    video_path = os.path.join(automark_dist, "showcase.mp4")
    if os.path.exists(video_path):
        return FileResponse(video_path, media_type="video/mp4")
    # Fallback to root video
    root_video = os.path.join(project_root, "Magic_Fill_video.mp4")
    if os.path.exists(root_video):
        return FileResponse(root_video, media_type="video/mp4")
    return Response(status_code=404)


@app.get("/", include_in_schema=False)
def serve_dashboard():
    # Prefer Automark compiled website
    automark_index = os.path.join(automark_dist, "index.html")
    if os.path.exists(automark_index):
        return FileResponse(automark_index)

    index_file = os.path.join(web_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse(
        status_code=200,
        content={"message": "Magic Fill Backend is Running. Web UI will be loaded."}
    )


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"], include_in_schema=False)
def serve_automark_pages(full_path: str, request: Request):
    clean_path = full_path.strip("/")

    # Do not serve HTML for unhandled API requests
    if clean_path.startswith("api/") or clean_path == "api":
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": f"API endpoint '/{clean_path}' not found",
                "error_code": "NOT_FOUND"
            }
        )

    if request.method not in ("GET", "HEAD"):
        return JSONResponse(
            status_code=405,
            content={"success": False, "message": "Method Not Allowed", "error_code": "METHOD_NOT_ALLOWED"}
        )

    # Check if the requested path matches an HTML page or static file in automark_dist
    if os.path.exists(automark_dist):
        # Direct file check (e.g. robots.txt, sitemap.xml)
        direct_file = os.path.join(automark_dist, clean_path)
        if os.path.isfile(direct_file):
            return FileResponse(direct_file)

        # Directory index.html check (e.g. /features -> /features/index.html)
        dir_index = os.path.join(automark_dist, clean_path, "index.html")
        if os.path.isfile(dir_index):
            return FileResponse(dir_index)

        # File with .html suffix
        html_file = os.path.join(automark_dist, f"{clean_path}.html")
        if os.path.isfile(html_file):
            return FileResponse(html_file)

    # Fallback to index.html for SPA/client routing if applicable
    automark_index = os.path.join(automark_dist, "index.html")
    if os.path.exists(automark_index):
        return FileResponse(automark_index)

    return Response(status_code=404)

