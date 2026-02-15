"""Email model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EmailClassification(str, enum.Enum):
    """Possible email classifications."""
    INQUIRY = "inquiry"
    MEETING_REQUEST = "meeting_request"
    COMPLAINT = "complaint"
    FOLLOW_UP = "follow_up"
    SPAM = "spam"
    OTHER = "other"


class EmailStatus(str, enum.Enum):
    """Email processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    DRAFTED = "drafted"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    SENT = "sent"
    REJECTED = "rejected"


class Email(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Email record fetched from Gmail."""

    __tablename__ = "emails"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    gmail_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str] = mapped_column(String(998), nullable=False, default="")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sender: Mapped[str] = mapped_column(String(320), nullable=False)
    recipient: Mapped[str | None] = mapped_column(String(320), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    classification: Mapped[EmailClassification | None] = mapped_column(
        Enum(EmailClassification, values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
    )
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[EmailStatus] = mapped_column(
        Enum(EmailStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=EmailStatus.PENDING,
        nullable=False,
    )
    draft_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="emails")  # noqa: F821
    agent_logs: Mapped[list["AgentLog"]] = relationship(  # noqa: F821
        back_populates="email", cascade="all, delete-orphan"
    )
