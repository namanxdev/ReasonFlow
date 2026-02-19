"""Email template model for reusable response templates."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class EmailTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Reusable email template with variable substitution support."""

    __tablename__ = "email_templates"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subject_template: Mapped[str] = mapped_column(
        String(998), nullable=False
    )  # RFC 2822 max
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # e.g., "sales", "support"
    variables: Mapped[list] = mapped_column(JSON, default=list)  # ["customer_name", "order_id"]
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    user: Mapped[User] = relationship(back_populates="email_templates")
