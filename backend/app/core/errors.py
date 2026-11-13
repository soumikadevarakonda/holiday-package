"""
Standard application errors and exception handling for Build My Holiday API.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application exception with structured error payload."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert error to uniform JSON response shape."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class NotFoundError(AppError):
    """Resource not found (HTTP 404)."""

    def __init__(self, message: str = "Resource not found", details: Any = None) -> None:
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details,
        )


class ConflictError(AppError):
    """State conflict or business rule violation (HTTP 409)."""

    def __init__(
        self,
        message: str = "Conflict occurred",
        code: str = "CONFLICT",
        details: Any = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=409,
            details=details,
        )


class ValidationError(AppError):
    """Invalid input or failed validation constraint (HTTP 422)."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class BadRequestError(AppError):
    """Bad request (HTTP 400)."""

    def __init__(self, message: str, code: str = "BAD_REQUEST", details: Any = None) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=400,
            details=details,
        )


class EngineUnavailableError(AppError):
    """Required engine dependency is awaiting integration (HTTP 503)."""

    def __init__(
        self,
        operation: str,
        message: str | None = None,
        details: Any = None,
    ) -> None:
        op_msg = message or (
            f"Package engine function for '{operation}' is not yet connected. "
            "Awaiting Person A's engine integration."
        )
        payload = details or {}
        if isinstance(payload, dict):
            payload["operation"] = operation
        super().__init__(
            message=op_msg,
            code="ENGINE_UNAVAILABLE",
            status_code=503,
            details=payload,
        )
