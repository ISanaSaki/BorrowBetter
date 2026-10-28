"""Shared test fixtures.

Owner: Sana (B).

The database must be migrated first (`alembic upgrade head`); CI does that, and
locally `pytest` is run after `make migrate`. Every test starts from an empty
schema — `TRUNCATE ... RESTART IDENTITY` is ~1ms and removes ordering surprises.
"""

from __future__ import annotations

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://borrowbetter:borrowbetter@127.0.0.1:5432/borrowbetter",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-characters")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.constants import ItemCategory, ItemCondition  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.item import Item  # noqa: E402
from app.models.user import User  # noqa: E402

# bcrypt is intentionally slow — hash once for the whole session.
PASSWORD_HASH = hash_password("Demo1234!")


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_db() -> None:
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE reservations, items, users RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _make_user(db, email: str, full_name: str) -> User:
    user = User(email=email, password_hash=PASSWORD_HASH, full_name=full_name)
    db.add(user)
    return user


@pytest.fixture()
def owner(db) -> User:
    user = _make_user(db, "sana@test.ir", "ثنا")
    db.commit()
    return user


@pytest.fixture()
def borrower(db) -> User:
    user = _make_user(db, "asra@test.ir", "اسرا")
    db.commit()
    return user


@pytest.fixture()
def stranger(db) -> User:
    user = _make_user(db, "stranger@test.ir", "غریبه")
    db.commit()
    return user


@pytest.fixture()
def item(db, owner) -> Item:
    obj = Item(
        owner_id=owner.id,
        title="دریل برقی بوش",
        description="دریل چکشی ۷۵۰ وات همراه با بیت‌ست کامل.",
        category=ItemCategory.TOOLS,
        condition=ItemCondition.GOOD,
        price_per_day=50_000,
        image_url="https://picsum.photos/seed/drill/600/400",
    )
    db.add(obj)
    db.commit()
    return obj


@pytest.fixture()
def borrower_factory(db):
    """Create N distinct borrowers in one round-trip (needed for 50-way races)."""
    created: list[User] = []

    def _make(count: int = 1) -> list[User]:
        users = [
            _make_user(db, f"borrower{len(created) + i}@test.ir", f"متقاضی {len(created) + i}")
            for i in range(count)
        ]
        db.commit()
        created.extend(users)
        return users

    return _make


@pytest.fixture()
def headers():
    def _headers(user: User) -> dict[str, str]:
        token, _ = create_access_token(user.id)
        return {"Authorization": f"Bearer {token}"}

    return _headers
