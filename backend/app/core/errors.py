"""One error shape for the whole API: {"code", "message", "details"}."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Raise anywhere in a request; the handler turns it into the standard error body."""

    def __init__(self, code: str, message: str, status_code: int = 400, details: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details if details is not None else {}


# Shortcuts for the codes in PRD section 10.
def not_found(message: str = "Not found", details: Any = None) -> AppError:
    return AppError("NOT_FOUND", message, 404, details)


def rule_violation(violations: list[dict]) -> AppError:
    return AppError("RULE_VIOLATION", "The change breaks one or more travel rules.", 409, {"violations": violations})


def version_conflict(current_version: int) -> AppError:
    return AppError("VERSION_CONFLICT", "The package was changed elsewhere. Reload it.", 409,
                    {"current_version": current_version})


def _body(code: str, message: str, details: Any) -> dict:
    return {"code": code, "message": message, "details": details}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        field_errors = {}
        for err in exc.errors():
            loc = [str(p) for p in err.get("loc", []) if p not in ("body", "query", "path")]
            field_errors[".".join(loc) or "request"] = err.get("msg", "Invalid value")
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
