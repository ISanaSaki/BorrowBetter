"""Registration and login (Backend A)."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.schemas.auth import LoginIn, RegisterIn, TokenOut
from app.schemas.common import DataResponse, ErrorResponse
from app.services.auth import authenticate, issue_token, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=DataResponse[TokenOut],
    status_code=status.HTTP_201_CREATED,
    summary="Register a user and receive a token",
    responses={
        409: {"model": ErrorResponse, "description": "Email already registered"},
        422: {"model": ErrorResponse, "description": "Invalid input"},
    },
)
def register(payload: RegisterIn, db: DbSession) -> DataResponse[TokenOut]:
    user = register_user(db, payload)
    return DataResponse[TokenOut](data=issue_token(user))


@router.post(
    "/login",
    response_model=DataResponse[TokenOut],
    summary="Log in and receive a token",
    responses={401: {"model": ErrorResponse, "description": "Incorrect email or password"}},
)
def login(payload: LoginIn, db: DbSession) -> DataResponse[TokenOut]:
    user = authenticate(db, str(payload.email), payload.password)
    return DataResponse[TokenOut](data=issue_token(user))
