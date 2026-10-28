"""FastAPI dependencies.

Owner: Asra (scaffold).
"""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False, description="JWT access token")


def get_db() -> Iterator[Session]:
    yield from get_session()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise AppError("UNAUTHORIZED", 401, "برای این کار باید وارد حساب کاربری شوید.")

    try:
        user_id = decode_access_token(credentials.credentials)
    except ValueError:
        raise AppError("UNAUTHORIZED", 401, "نشست شما منقضی شده است؛ دوباره وارد شوید.")

    user = db.get(User, user_id)
    if user is None:
        raise AppError("UNAUTHORIZED", 401, "کاربر یافت نشد؛ دوباره وارد شوید.")
    return user
