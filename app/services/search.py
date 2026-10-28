"""Reusable text search helpers (catalog + AI assistant)."""

from __future__ import annotations

import re

from sqlalchemy import ColumnElement, or_

from app.models.item import Item

_SPACES = re.compile(r"\s+")
_LIKE_SPECIALS = re.compile(r"([\\%_])")


def normalize_query(raw: str | None) -> str:
    """Collapse whitespace and normalize zero-width characters."""
    if not raw:
        return ""
    normalized = raw.replace("\u200c", " ").replace("\u200f", "").replace("\u200e", "")
    return _SPACES.sub(" ", normalized).strip()


def like_pattern(normalized: str) -> str:
    """Escape % and _ so user input cannot inject LIKE wildcards."""
    return f"%{_LIKE_SPECIALS.sub(r'\\\1', normalized)}%"


def text_filter(query: str | None) -> ColumnElement[bool] | None:
    normalized = normalize_query(query)
    if not normalized:
        return None
    pattern = like_pattern(normalized)
    return or_(
        Item.title.ilike(pattern, escape="\\"),
        Item.description.ilike(pattern, escape="\\"),
    )
