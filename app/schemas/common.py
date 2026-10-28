"""Response envelopes, pagination and the shared UTC datetime type.

Contract: keys are always present; unknown values are `null`, never omitted.
Both the historical names (`Envelope`, `PageEnvelope`, `Meta`, `UtcDatetime`)
and the descriptive ones (`DataResponse`, `Page`, `PageMeta`, `UtcDateTime`)
refer to the same objects, so the platform and booking layers share one wire format.
"""

from __future__ import annotations

from datetime import datetime, timezone
from math import ceil
from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer, WithJsonSchema

T = TypeVar("T")


def ensure_utc(value: Any) -> datetime:
    """Accept ISO-8601 strings; treat naive datetimes as UTC."""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Invalid date/time, ISO-8601 expected.") from exc
    if not isinstance(value, datetime):
        raise ValueError("Invalid date/time.")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def serialize_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def iso_utc_z(value: datetime) -> str:
    """Alias kept for the platform layer."""
    return serialize_utc(value)


UtcDatetime = Annotated[
    datetime,
    BeforeValidator(ensure_utc),
    PlainSerializer(serialize_utc, return_type=str),
    WithJsonSchema(
        {"type": "string", "format": "date-time", "examples": ["2026-11-01T10:00:00Z"]}
    ),
]

UtcDateTime = UtcDatetime


class Meta(BaseModel):
    page: int = Field(default=1, ge=1, examples=[1])
    limit: int = Field(default=20, ge=1, le=100, examples=[20])
    total: int = Field(default=0, ge=0, examples=[12])
    total_pages: int = Field(default=0, ge=0, examples=[1])
    has_next: bool = Field(default=False)

    @classmethod
    def build(cls, page: int, limit: int, total: int) -> "Meta":
        total_pages = ceil(total / limit) if limit > 0 else 0
        return cls(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page * limit < total,
        )


PageMeta = Meta


class Envelope(BaseModel, Generic[T]):
    data: T


DataResponse = Envelope


class PageEnvelope(BaseModel, Generic[T]):
    data: list[T]
    meta: Meta


Page = PageEnvelope


class ErrorBody(BaseModel):
    code: str = Field(examples=["VALIDATION_ERROR"])
    message: str = Field(examples=["Invalid input."])
    details: dict[str, Any] | None = Field(default=None)


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "SLOT_CONFLICT",
                    "message": "This time slot is already booked.",
                    "details": {"suggestions": []},
                }
            }
        }
    )

    error: ErrorBody


ErrorResponse = ErrorEnvelope


class HealthOut(BaseModel):
    status: str = Field(examples=["ok"], description="ok | degraded")
    db: str = Field(examples=["up"], description="up | down")
    version: str = Field(examples=["0.1.0"])
    time: UtcDateTime


class DeactivateOut(BaseModel):
    id: int
    is_active: bool
