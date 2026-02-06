"""Tool execution log model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ToolExecution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Log entry for each tool invoked during an agent step."""

    __tablename__ = "tool_executions"

    agent_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_logs.id"), nullable=False, index=True
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latency_ms: Mapped[float] = mapped_column(nullable=False, default=0.0)

    # Relationships
    agent_log: Mapped["AgentLog"] = relationship(  # noqa: F821
        back_populates="tool_executions"
    )
