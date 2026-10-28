"""Version 1 router assembly.

The only place where team routers are wired together.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.routers import auth, items, reservations, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(items.catalog_router)
api_router.include_router(items.router)
api_router.include_router(items.me_router)
api_router.include_router(reservations.router)
