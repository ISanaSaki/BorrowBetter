"""Current user profile (Backend A)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.schemas.common import DataResponse, ErrorResponse
from app.schemas.user import UserOut

router = APIRouter(prefix="/me", tags=["me"])


@router.get(
    "",
    response_model=DataResponse[UserOut],
    summary="Get my profile",
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid token"}},
)
def read_me(user: CurrentUser) -> DataResponse[UserOut]:
    return DataResponse[UserOut](data=UserOut.model_validate(user))
