"""Registration, login and token issuing (Backend A)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError, sqlstate
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterIn, TokenOut
from app.schemas.user import UserOut


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == normalize_email(email)))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def register_user(db: Session, payload: RegisterIn) -> User:
    email = normalize_email(str(payload.email))

    if get_user_by_email(db, email) is not None:
        raise AppError(
            "EMAIL_ALREADY_EXISTS",
            409,
            "This email is already registered. Sign in or use another address.",
            {"field": "email"},
        )

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if sqlstate(exc) == "23505":  # unique_violation
            raise AppError(
                "EMAIL_ALREADY_EXISTS",
                409,
                "This email is already registered. Sign in or use another address.",
                {"field": "email"},
            ) from exc
        raise
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    # Same message for both cases so we never leak whether an account exists.
    if user is None or not verify_password(password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", 401, "Incorrect email or password.")
    return user


def issue_token(user: User) -> TokenOut:
    token, expires_in = create_access_token(user.id)
    return TokenOut(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserOut.model_validate(user),
    )
