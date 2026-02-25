"""SQLAlchemy base model and common mixins."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """Mixin that adds a UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class SoftDeleteMixin:
    """Mixin that adds soft delete capability to models (DB-NEW-5 fix).

    Instead of permanently deleting records, sets deleted_at timestamp.
    Query filters automatically exclude soft-deleted records.

    Usage:
        class MyModel(Base, SoftDeleteMixin):
            __tablename__ = "my_table"
            ...

        # Query only non-deleted (default)
        result = await db.execute(select(MyModel))

        # Include deleted
        result = await db.execute(select(MyModel).execution_options(include_deleted=True))

        # Soft delete
        await obj.soft_delete(db)

        # Restore
        await obj.restore(db)
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,  # Index for efficient filtering
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None

    async def soft_delete(self, db) -> None:
        """Soft delete this record."""
        self.deleted_at = datetime.now()
        await db.flush()

    async def restore(self, db) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
        await db.flush()

    @classmethod
    def filter_not_deleted(cls, query):
        """Add filter to exclude deleted records from query."""
        return query.where(cls.deleted_at.is_(None))

    @classmethod
    def filter_deleted(cls, query):
        """Add filter to include only deleted records."""
        return query.where(cls.deleted_at.is_not(None))
