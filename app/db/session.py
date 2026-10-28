"""Engine / session factory.

Owner: Asra (scaffold). Tuning matters for the 50-request concurrency test:
the pool must be big enough that requests *queue on the row lock*, not on the
pool — otherwise the test measures connection starvation instead of booking.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=1800,
    echo=settings.db_echo,
    # All timestamps are UTC end-to-end (spec §0.8). Forcing the session TZ
    # keeps psycopg from handing back datetimes in the server's local zone.
    connect_args={
        "options": "-c timezone=UTC",
        "application_name": "borrowbetter-api",
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,  # after commit we serialise without re-selecting
)


def get_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
