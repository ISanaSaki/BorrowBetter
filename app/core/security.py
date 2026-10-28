"""Password hashing (bcrypt) and JWT issuing/validation."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.errors import Unauthorized

_BCRYPT_MAX_BYTES = 72  # inherent bcrypt input limit


def _prepare(raw_password: str) -> bytes:
    # bcrypt only reads the first 72 bytes; truncating explicitly avoids
    # hard errors on newer releases and keeps hashes reproducible.
    return raw_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(raw_password: str) -> str:
    rounds = get_settings().bcrypt_rounds
    return bcrypt.hashpw(_prepare(raw_password), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def verify_password(raw_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(raw_password), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, *, expires_delta: timedelta | None = None) -> tuple[str, int]:
    """Returns (token, lifetime in seconds)."""
    settings = get_settings()
    delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + delta).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, int(delta.total_seconds())


def decode_token(token: str) -> int:
    """Returns the user id, raises `Unauthorized` otherwise."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise Unauthorized("Session expired. Please sign in again.", {"reason": "token_expired"}) from exc
    except jwt.PyJWTError as exc:
        raise Unauthorized("Invalid token.", {"reason": "invalid_token"}) from exc

    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise Unauthorized("Invalid token.", {"reason": "invalid_subject"}) from exc
