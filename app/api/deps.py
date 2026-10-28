"""Shared FastAPI dependencies (Backend A)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import Forbidden, NotFound, Unauthorized
from app.core.security import decode_token
from app.db.session import get_db
from app.models.item import Item
from app.models.user import User
from app.services.auth import get_user_by_id

# HTTPBearer (not OAuth2PasswordBearer) because login is JSON based: the Swagger
# "Authorize" dialog then accepts a raw token.
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="JWT from `POST /api/v1/auth/login`",
)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User:
    if credentials is None or not credentials.credentials:
        raise Unauthorized("Authentication required.")

    user = get_user_by_id(db, decode_token(credentials.credentials))
    if user is None:
        raise Unauthorized("User for this token no longer exists.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_owned_item(item_id: int, db: DbSession, user: CurrentUser) -> Item:
    """Loads an item and checks ownership: 404 if missing, 403 if not the owner."""
    item = db.get(Item, item_id)
    if item is None:
        raise NotFound("Item not found.")
    if item.owner_id != user.id:
        raise Forbidden("Only the item owner can perform this action.")
    return item
