from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import UtcDateTime


class UserBrief(BaseModel):
    """Lightweight user representation (item owner in responses)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str


class UserOut(BaseModel):
    """Public user payload - never exposes `password_hash`."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[2])
    email: EmailStr = Field(examples=["user@example.com"])
    full_name: str = Field(examples=["Alex Carter"])
    phone: str | None = Field(default=None, examples=["09121234567"])
    created_at: UtcDateTime
