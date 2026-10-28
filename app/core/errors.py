"""Uniform error envelope and domain error primitives.

Every failure - domain, validation or unexpected - is returned as:

    {"error": {"code": "...", "message": "...", "details": {...} | null}}

Backend B only raises `AppError` (or the helpers below) and never builds
responses itself.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """A controlled domain error that is safe to show to the end user."""

    def __init__(
        self,
        code: str,
        status_code: int,
        message: str,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.message = message
        self.details = details
        self.headers = headers

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"AppError(code={self.code!r}, status={self.status_code})"


# --- Helper constructors used by the booking engine ------------------------- #
def not_found(
    message: str = "Resource not found.", details: dict[str, Any] | None = None
) -> AppError:
    return AppError("NOT_FOUND", 404, message, details)


def forbidden(
    message: str = "You do not have permission to perform this action.",
    details: dict[str, Any] | None = None,
) -> AppError:
    return AppError("FORBIDDEN", 403, message, details)


def validation_error(message: str, fields: dict[str, str] | None = None) -> AppError:
    details = {"fields": fields} if fields else None
    return AppError("VALIDATION_ERROR", 422, message, details)


class NotFound(AppError):
    def __init__(
        self, message: str = "Resource not found.", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__("NOT_FOUND", 404, message, details)


class Forbidden(AppError):
    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("FORBIDDEN", 403, message, details)


class Unauthorized(AppError):
    def __init__(
        self,
        message: str = "Authentication required.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__("UNAUTHORIZED", 401, message, details, headers={"WWW-Authenticate": "Bearer"})


def sqlstate(exc: BaseException) -> str | None:
    """Driver independent SQLSTATE (psycopg3 -> sqlstate, psycopg2 -> pgcode)."""
    orig = getattr(exc, "orig", exc)
    return getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
        headers=headers,
    )


# --- Validation messages (stable, machine friendly) ------------------------- #
_FIELD_MESSAGES: dict[str, str] = {
    "missing": "This field is required.",
    "string_too_short": "Text is shorter than the allowed minimum.",
    "string_too_long": "Text is longer than the allowed maximum.",
    "string_type": "Value must be a string.",
    "int_parsing": "Must be a valid integer.",
    "int_type": "Value must be an integer.",
    "float_parsing": "Must be a valid number.",
    "greater_than": "Must be greater than the allowed minimum.",
    "greater_than_equal": "Must be greater than or equal to the allowed minimum.",
    "less_than": "Must be less than the allowed maximum.",
    "less_than_equal": "Must be less than or equal to the allowed maximum.",
    "bool_parsing": "Must be a valid boolean.",
    "bool_type": "Must be true or false.",
    "enum": "Value is not one of the allowed options.",
    "json_invalid": "Request body is not valid JSON.",
    "extra_forbidden": "This field is not part of the contract.",
    "datetime_parsing": "Invalid date/time. Use ISO-8601, e.g. 2026-11-01T10:00:00Z.",
    "datetime_from_date_parsing": "Invalid date/time. ISO-8601 expected.",
    "datetime_type": "Invalid date/time. ISO-8601 expected.",
    "date_parsing": "Invalid date.",
    "url_parsing": "Invalid URL.",
    "list_type": "Value must be a list.",
    "dict_type": "Value must be an object.",
    "value_error": "Invalid value.",
}

_LOC_NAMES = {"body", "query", "path", "header", "cookie"}


def _field_path(loc: tuple[Any, ...]) -> str:
    parts = [str(part) for part in loc if str(part) not in _LOC_NAMES]
    return ".".join(parts) or "body"


def _humanize(err: dict[str, Any]) -> str:
    err_type = str(err.get("type", ""))
    raw = str(err.get("msg", ""))

    if err_type == "value_error":
        message = raw.removeprefix("Value error, ").strip()
        if message and all(ord(ch) < 128 for ch in message):
            return message
        return "Invalid value."

    return _FIELD_MESSAGES.get(err_type, "Invalid value.")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message, exc.details, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields: dict[str, str] = {}
        for err in exc.errors():
            key = _field_path(tuple(err.get("loc", ())))
            fields.setdefault(key, _humanize(err))
        return error_response(
            422,
            "VALIDATION_ERROR",
            "Invalid input. Fix the highlighted fields.",
            {"fields": fields},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_by_status = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMITED",
        }
        default_messages = {
            400: "Bad request.",
            401: "Authentication required.",
            403: "You do not have permission to perform this action.",
            404: "The requested resource was not found.",
            405: "Method not allowed for this route.",
            409: "Request conflicts with the current state of the resource.",
            422: "Invalid input.",
            429: "Too many requests. Try again later.",
        }
        detail = exc.detail if isinstance(exc.detail, str) else None
        is_ascii = bool(detail) and all(ord(ch) < 128 for ch in detail or "")
        message = detail if is_ascii else default_messages.get(exc.status_code, "Request error.")
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return error_response(
            exc.status_code, code_by_status.get(exc.status_code, "HTTP_ERROR"), message, None, headers
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "-")
        logger.exception("Unhandled error rid=%s %s %s", request_id, request.method, request.url.path)
        return error_response(
            500,
            "INTERNAL_ERROR",
            "Internal server error. Please try again later.",
            {"request_id": request_id},
        )
