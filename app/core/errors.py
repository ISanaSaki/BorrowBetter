"""Error primitives — one envelope for the whole API (spec §7.24).

Owner: Asra (scaffold). B raises `AppError` only; never builds responses.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """A domain error that is safe to show to the end user."""

    def __init__(
        self,
        code: str,
        status_code: int,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.message = message
        self.details = details

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"AppError(code={self.code!r}, status={self.status_code})"


def not_found(message: str = "موردی پیدا نشد.") -> AppError:
    return AppError("NOT_FOUND", 404, message)


def forbidden(message: str = "شما مجاز به انجام این کار نیستید.") -> AppError:
    return AppError("FORBIDDEN", 403, message)


def validation_error(message: str, fields: dict[str, str] | None = None) -> AppError:
    details = {"fields": fields} if fields else None
    return AppError("VALIDATION_ERROR", 422, message, details)
