"""Item model.

Owner: Asra (scaffold).

The PostgreSQL enum types are created by migration 0001, so every ENUM here is
`create_type=False` — SQLAlchemy must never try to emit its own DDL.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Identity, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ItemCategory, ItemCondition
from app.db.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from app.models.user import User


def _values(enum_cls: type) -> list[str]:
    return [member.value for member in enum_cls]


item_category_enum = PgEnum(
    ItemCategory,
    name="item_category",
    create_type=False,
    values_callable=_values,
)

item_condition_enum = PgEnum(
    ItemCondition,
    name="item_condition",
    create_type=False,
    values_callable=_values,
)


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    category: Mapped[ItemCategory] = mapped_column(item_category_enum, nullable=False)
    condition: Mapped[ItemCondition] = mapped_column(
        item_condition_enum, nullable=False, server_default=text("'good'")
    )
    price_per_day: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    owner: Mapped["User"] = relationship(back_populates="items")
