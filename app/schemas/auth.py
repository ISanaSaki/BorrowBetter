from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.user import UserOut


class RegisterIn(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "email": "alex@example.com",
                "password": "Demo1234!",
                "full_name": "Alex Carter",
                "phone": "09121234567",
            }
        },
    )

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=80)
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, value: str) -> str:
        if not any(ch.isalpha() for ch in value):
            raise ValueError("Password must contain at least one letter.")
        if not any(ch.isdigit() for ch in value):
            raise ValueError("Password must contain at least one digit.")
        return value

    @field_validator("phone")
    @classmethod
    def _phone_format(cls, value: str | None) -> str | None:
        if value is None:
            return None
        digits = value.replace("-", "").replace(" ", "")
        if not digits.isdigit() or not 10 <= len(digits) <= 11:
            raise ValueError("Phone number is not valid.")
        return digits


class LoginIn(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={"example": {"email": "alex@example.com", "password": "Demo1234!"}},
    )

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str = Field(examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6..."])
    token_type: str = Field(default="bearer", examples=["bearer"])
    expires_in: int = Field(examples=[86400], description="Token lifetime in seconds")
    user: UserOut
