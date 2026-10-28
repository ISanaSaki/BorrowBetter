"""v1 router — mounts every router under /api/v1.

Owner: Asra (scaffold).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.routers import auth, items, reservations, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(items.router, tags=["items"])
# Sana's booking engine: /reservations/*, /me/reservations, /items/{id}/availability
api_router.include_router(reservations.router)
