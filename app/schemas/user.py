"""User schemas.

Owner: Asra (scaffold).  `password_hash` never leaves the process.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import UtcDatetime


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    phone: str | None
    created_at: UtcDatetime


class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=2, max_length=80)
    phone: str | None = Field(default=None, max_length=20)


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=72)
