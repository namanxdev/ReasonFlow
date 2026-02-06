"""Embedding model for vector search."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# pgvector column type will be added when pgvector extension is available
# For now we store embeddings as JSON; migration handles the vector column


class Embedding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Vector embedding for similarity search."""

    __tablename__ = "embeddings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "email", "crm", "calendar"
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
