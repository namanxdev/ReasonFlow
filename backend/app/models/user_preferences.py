"""User preferences model for settings."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserPreferences(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User preferences and settings for the ReasonFlow agent.

    Stores configuration options like auto-approval thresholds, sync frequency,
    notification preferences, and timezone settings.
    """

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Auto-approval threshold (0.0-1.0) - confidence level required for auto-approval
    auto_approval_threshold: Mapped[float] = mapped_column(
        default=0.9,
        nullable=False,
    )

    # Email sync frequency in minutes
    email_sync_frequency_minutes: Mapped[int] = mapped_column(
        default=15,
        nullable=False,
    )

    # Notification settings stored as JSON
    # Expected format: {"email": bool, "push": bool, "digest": bool}
    notification_settings: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # User timezone (IANA timezone identifier, e.g., "America/New_York")
    timezone: Mapped[str] = mapped_column(
        String(100),
        default="UTC",
        nullable=False,
    )

    # Daily digest email notification
    daily_digest_enabled: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Automatically classify emails during sync
    auto_classify_on_sync: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Maximum number of auto-responses per day
    max_auto_responses_per_day: Mapped[int] = mapped_column(
        default=50,
        nullable=False,
    )

    # Relationship back to user
    user: Mapped[User] = relationship(
        back_populates="preferences",
        lazy="joined",
    )
