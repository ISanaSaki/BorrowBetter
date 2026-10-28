"""Reservation model — the booking engine's only table.

Owner: Sana (B).  Migration: alembic/versions/0002_reservations.py

Note: the *real* overlap guarantee lives in PostgreSQL
(`EXCLUDE USING gist (item_id WITH =, tstzrange(start_at, end_at, '[)') WITH &&)
WHERE status IN ('pending','approved','active')`). This model only mirrors it.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ReservationStatus
from app.db.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from app.models.item import Item
    from app.models.user import User


def _values(enum_cls: type) -> list[str]:
    return [member.value for member in enum_cls]


reservation_status_enum = PgEnum(
    ReservationStatus,
    name="reservation_status",
    create_type=False,
    values_callable=_values,
)


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)

    item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("items.id", ondelete="CASCADE"), nullable=False
    )
    borrower_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[ReservationStatus] = mapped_column(
        reservation_status_enum, nullable=False, server_default=text("'pending'")
    )
    total_price: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # TEXT + CHECK in the DB; validated at the schema layer (spec §5.4).
    returned_by: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    handover_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    item: Mapped["Item"] = relationship(foreign_keys=[item_id])
    borrower: Mapped["User"] = relationship(foreign_keys=[borrower_id])

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Reservation id={self.id} item={self.item_id} status={self.status}>"
