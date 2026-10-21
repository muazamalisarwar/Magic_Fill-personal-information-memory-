from typing import Any, Optional


class AppException(Exception):
    """Base application exception for handled domain and business logic errors."""
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 400,
        details: Optional[Any] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class UserNotFoundException(AppException):
    """Exception raised when a user is not found."""
    def __init__(self, user_id: int):
        super().__init__(
            message=f"User with ID {user_id} was not found",
            error_code="USER_NOT_FOUND",
            status_code=404
        )


class PersonalInfoNotFoundException(AppException):
    """Exception raised when personal info for a user is not found."""
    def __init__(self, user_id: int):
        super().__init__(
            message=f"Personal information for user ID {user_id} was not found",
            error_code="PERSONAL_INFO_NOT_FOUND",
            status_code=404
        )


class PersonalInfoAlreadyExistsException(AppException):
    """Exception raised when attempting to create duplicate personal info for a user."""
    def __init__(self, user_id: int):
        super().__init__(
            message=f"Personal information already exists for user ID {user_id}. Use PUT to update.",
            error_code="PERSONAL_INFO_ALREADY_EXISTS",
            status_code=400
        )


class ExperienceNotFoundException(AppException):
    """Exception raised when an experience is not found."""
    def __init__(self, experience_id: int):
        super().__init__(
            message=f"Experience with ID {experience_id} was not found",
            error_code="EXPERIENCE_NOT_FOUND",
            status_code=404
        )


class CustomFieldNotFoundException(AppException):
    """Exception raised when a custom field is not found."""
    def __init__(self, field_id: int):
        super().__init__(
            message=f"Custom field with ID {field_id} was not found",
            error_code="CUSTOM_FIELD_NOT_FOUND",
            status_code=404
        )


class BadRequestException(AppException):
    """General bad request exception."""
    def __init__(self, message: str, error_code: str = "BAD_REQUEST", details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details=details
        )


class DocumentNotFoundException(AppException):
    """Exception raised when a document is not found."""
    def __init__(self, document_id: int):
        super().__init__(
            message=f"Document with ID {document_id} was not found",
            error_code="DOCUMENT_NOT_FOUND",
            status_code=404
        )


class NotFoundException(AppException):
    """General not found exception."""
    def __init__(self, message: str = "Resource not found", error_code: str = "NOT_FOUND"):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=404
        )


class AuthenticationException(AppException):
    """Exception raised when authentication fails or token is invalid/expired."""
    def __init__(self, message: str = "Authentication required or invalid credentials", error_code: str = "UNAUTHORIZED"):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401
        )


class DuplicateEmailException(AppException):
    """Exception raised when an email is already registered."""
    def __init__(self, email: str):
        super().__init__(
            message=f"An account with email '{email}' already exists. Please sign in instead.",
            error_code="DUPLICATE_EMAIL",
            status_code=400
        )


class InvalidAuthCodeException(AppException):
    """Exception raised when an extension single-use authorization code is invalid or expired."""
    def __init__(self, message: str = "Authorization code is invalid, already used, or expired"):
        super().__init__(
            message=message,
            error_code="INVALID_AUTH_CODE",
            status_code=400
        )



