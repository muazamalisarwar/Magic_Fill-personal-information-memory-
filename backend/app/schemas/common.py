from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard generic API response wrapper for successful operations."""
    success: bool = True
    message: str
    data: Optional[T] = None

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standard API response wrapper for error responses."""
    success: bool = False
    message: str
    error_code: str
    details: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """Response model for system health check endpoint."""
    success: bool = True
    message: str = "Backend is running"
    status: str = "healthy"
