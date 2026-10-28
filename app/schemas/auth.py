"""Auth payloads.

Owner: Asra (scaffold).
"""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.user import UserOut


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
