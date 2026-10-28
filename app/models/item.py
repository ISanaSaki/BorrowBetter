from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ItemCategory, ItemCondition
from app.db.base import Base, BigIntPk

if TYPE_CHECKING:  # pragma: no cover
    from app.models.user import User


def _enum_values(enum_cls: type) -> list[str]:
    """Store enum values (tools), not member names (TOOLS)."""
    return [member.value for member in enum_cls]


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("length(title) BETWEEN 3 AND 120", name="title_length"),
        CheckConstraint("price_per_day >= 0", name="price_non_negative"),
        Index("ix_items_owner_active", "owner_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    category: Mapped[ItemCategory] = mapped_column(
        Enum(ItemCategory, name="item_category", values_callable=_enum_values, native_enum=True),
        nullable=False,
        index=True,
    )
    condition: Mapped[ItemCondition] = mapped_column(
        Enum(ItemCondition, name="item_condition", values_callable=_enum_values, native_enum=True),
        nullable=False,
        server_default=ItemCondition.GOOD.value,
    )
    price_per_day: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true(), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Many-to-one and always needed for serialization. `selectin` loads owners in a
    # single extra query and keeps `SELECT ... FOR UPDATE` on items legal: PostgreSQL
    # rejects FOR UPDATE on the nullable side of an outer join, which a joined eager
    # load would introduce. It also avoids the N+1 problem.
    owner: Mapped[User] = relationship(back_populates="items", lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Item id={self.id} title={self.title!r} active={self.is_active}>"
