"""User model."""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Registered user with OAuth credentials."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    oauth_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    oauth_refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    emails: Mapped[list[Email]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    email_templates: Mapped[list[EmailTemplate]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    preferences: Mapped[UserPreferences] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
