"""Auth endpoints.

Owner: Asra (scaffold).  Contract: spec §7.4 – §7.5.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.auth import TokenOut
from app.schemas.common import Envelope
from app.schemas.user import UserLogin, UserOut, UserRegister
from app.services import auth as auth_service

router = APIRouter()


def _token_out(user, token: str, expires_in: int) -> TokenOut:
    return TokenOut(
        access_token=token,
        expires_in=expires_in,
        user=UserOut(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            created_at=user.created_at,
        ),
    )


@router.post("/register", response_model=Envelope[TokenOut], status_code=201, summary="Register")
def register(payload: UserRegister, db: Session = Depends(get_db)) -> dict:
    user, token, expires_in = auth_service.register(db, payload)
    return {"data": _token_out(user, token, expires_in)}


@router.post("/login", response_model=Envelope[TokenOut], summary="Log in")
def login(payload: UserLogin, db: Session = Depends(get_db)) -> dict:
    user, token, expires_in = auth_service.login(db, payload)
    return {"data": _token_out(user, token, expires_in)}
