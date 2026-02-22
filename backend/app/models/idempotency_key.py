"""Idempotency key model for preventing duplicate operations."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class IdempotencyKey(Base, TimestampMixin):
    """Tracks idempotency keys to prevent duplicate email dispatches.

    Uses INSERT ... ON CONFLICT DO NOTHING for atomic check-and-set.
    """

    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
