"""One error shape for the whole API: {"code", "message", "details"}.

Raise an AppError subclass anywhere in a request; register_error_handlers() turns it into the response.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Base application error with the structured payload."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500,
                 details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details if details is not None else {}

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


class NotFoundError(AppError):
    """404 NOT_FOUND."""

    def __init__(self, message: str = "Resource not found", details: Any = None) -> None:
        super().__init__(message, "NOT_FOUND", 404, details)


class ConflictError(AppError):
    """409: business conflict (RULE_VIOLATION, VERSION_CONFLICT, SOLD_OUT, …)."""

    def __init__(self, message: str = "Conflict occurred", code: str = "CONFLICT", details: Any = None) -> None:
        super().__init__(message, code, 409, details)


class ValidationError(AppError):
    """422: a valid request shape that cannot be applied (e.g. an impossible change)."""

    def __init__(self, message: str, code: str = "INVALID_INPUT", details: Any = None) -> None:
        super().__init__(message, code, 422, details)


class BadRequestError(AppError):
    """400 BAD_REQUEST."""

    def __init__(self, message: str, code: str = "BAD_REQUEST", details: Any = None) -> None:
        super().__init__(message, code, 400, details)


class EngineUnavailableError(AppError):
    """503: the package engine could not be imported."""

    def __init__(self, operation: str, message: str | None = None, details: Any = None) -> None:
        payload = dict(details or {})
        payload["operation"] = operation
        super().__init__(message or f"The package engine is not available for '{operation}'.",
                         "ENGINE_UNAVAILABLE", 503, payload)


def _body(code: str, message: str, details: Any) -> dict:
    return jsonable_encoder({"code": code, "message": message, "details": details})


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        field_errors = {}
        for err in exc.errors():
            loc = [str(p) for p in err.get("loc", []) if p not in ("body", "query", "path")]
            msg = str(err.get("msg", "Invalid value")).removeprefix("Value error, ")
            field_errors[".".join(loc) or "request"] = msg
        return JSONResponse(status_code=422, content=_body("INVALID_INPUT", "Some fields are not valid.",
                                                           {"field_errors": field_errors}))

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        code = "NOT_FOUND" if exc.status_code == 404 else f"HTTP_{exc.status_code}"
        return JSONResponse(status_code=exc.status_code, content=_body(code, str(exc.detail), {}))

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception):
        return JSONResponse(status_code=500, content=_body("INTERNAL_ERROR", "Unexpected server error.",
                                                           {"type": type(exc).__name__}))
