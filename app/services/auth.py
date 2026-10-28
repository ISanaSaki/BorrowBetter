"""Registration / login.

Owner: Asra (scaffold).
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserLogin, UserRegister

_LETTER = re.compile(r"[^\W\d_]", re.UNICODE)
_DIGIT = re.compile(r"\d")


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _check_password_strength(password: str) -> None:
    if not _LETTER.search(password) or not _DIGIT.search(password):
        raise AppError(
            "VALIDATION_ERROR",
            422,
            "رمز عبور باید حداقل یک حرف و یک رقم داشته باشد.",
            details={"fields": {"password": "حداقل یک حرف و یک رقم لازم است."}},
        )


def register(db: Session, payload: UserRegister) -> tuple[User, str, int]:
    email = _normalize_email(payload.email)
    _check_password_strength(payload.password)

    exists = db.scalar(select(User.id).where(User.email == email))
    if exists is not None:
        raise AppError("EMAIL_ALREADY_EXISTS", 409, "این ایمیل قبلاً ثبت شده است.")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        phone=payload.phone,
    )
    db.add(user)
    try:
        db.commit()
    except Exception as exc:  # unique race between two identical sign-ups
        db.rollback()
        raise AppError("EMAIL_ALREADY_EXISTS", 409, "این ایمیل قبلاً ثبت شده است.") from exc

    token, expires_in = create_access_token(user.id)
    return user, token, expires_in


def login(db: Session, payload: UserLogin) -> tuple[User, str, int]:
    email = _normalize_email(payload.email)
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", 401, "ایمیل یا رمز عبور اشتباه است.")

    token, expires_in = create_access_token(user.id)
    return user, token, expires_in
