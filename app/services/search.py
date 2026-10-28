"""Shared text search helper (also used as the AI module's fallback).

Owner: Asra (scaffold).
"""

from __future__ import annotations

from sqlalchemy import or_

from app.models.item import Item


def text_search_clause(term: str):
    """ILIKE on title/description — the fallback when TF-IDF finds nothing."""
    pattern = f"%{term.strip()}%"
    return or_(Item.title.ilike(pattern), Item.description.ilike(pattern))
