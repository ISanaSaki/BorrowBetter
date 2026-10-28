"""Model registry for Alembic and `Base.metadata`.

The `reservation` model belongs to Backend B and may not exist yet, so importing
it is optional; this keeps the platform branch runnable on its own.
"""

from __future__ import annotations

from app.db.base import Base
from app.models.item import Item
from app.models.user import User

__all__ = ["Base", "Item", "User"]

try:  # pragma: no cover - optional, owned by Backend B
    from app.models.reservation import Reservation  # noqa: F401

    __all__.append("Reservation")
except ImportError:
    pass
