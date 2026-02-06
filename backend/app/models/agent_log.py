"""Agent execution log model."""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AgentLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Log entry for each agent workflow step."""

    __tablename__ = "agent_logs"

    email_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emails.id"), nullable=False, index=True
    )
    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    step_order: Mapped[int] = mapped_column(nullable=False, default=0)
    input_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Relationships
    email: Mapped["Email"] = relationship(back_populates="agent_logs")  # noqa: F821
    tool_executions: Mapped[list["ToolExecution"]] = relationship(  # noqa: F821
        back_populates="agent_log", cascade="all, delete-orphan"
    )
