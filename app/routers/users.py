"""Current-user endpoint.

Owner: Asra (scaffold).  Contract: spec §7.6.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.common import Envelope
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/me", response_model=Envelope[UserOut], summary="Current user profile")
def me(user: User = Depends(get_current_user)) -> dict:
    return {
        "data": UserOut(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            created_at=user.created_at,
        )
    }
