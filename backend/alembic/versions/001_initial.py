"""initial schema - users, emails, agent_logs, tool_executions, embeddings

Revision ID: 001_initial
Revises: None
Create Date: 2026-02-06
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID

from alembic import op

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Users table
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("oauth_token_encrypted", sa.Text, nullable=True),
        sa.Column("oauth_refresh_token_encrypted", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Emails table
    op.create_table(
        "emails",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("gmail_id", sa.String(255), unique=True, nullable=False),
        sa.Column("thread_id", sa.String(255), nullable=True),
        sa.Column("subject", sa.String(998), nullable=False, server_default=""),
        sa.Column("body", sa.Text, nullable=False, server_default=""),
        sa.Column("sender", sa.String(320), nullable=False),
        sa.Column("recipient", sa.String(320), nullable=True),
        sa.Column(
            "received_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "classification",
            sa.Enum(
                "inquiry", "meeting_request", "complaint",
                "follow_up", "spam", "other",
                name="emailclassification",
            ),
            nullable=True,
        ),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "processing", "drafted", "needs_review",
                "approved", "sent", "rejected",
                name="emailstatus",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("draft_response", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_emails_user_id", "emails", ["user_id"])

    # Agent logs table
    op.create_table(
        "agent_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email_id", UUID(as_uuid=True), sa.ForeignKey("emails.id"), nullable=False),
        sa.Column("trace_id", UUID(as_uuid=True), nullable=False),
        sa.Column("step_name", sa.String(100), nullable=False),
        sa.Column("step_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("input_state", JSON, nullable=True),
        sa.Column("output_state", JSON, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("latency_ms", sa.Float, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agent_logs_email_id", "agent_logs", ["email_id"])
    op.create_index("ix_agent_logs_trace_id", "agent_logs", ["trace_id"])

    # Tool executions table
    op.create_table(
        "tool_executions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "agent_log_id", UUID(as_uuid=True),
            sa.ForeignKey("agent_logs.id"), nullable=False,
        ),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("params", JSON, nullable=True),
        sa.Column("result", JSON, nullable=True),
        sa.Column("success", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("latency_ms", sa.Float, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tool_executions_agent_log_id", "tool_executions", ["agent_log_id"])

    # Embeddings table (pgvector)
    op.create_table(
        "embeddings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=False),
        sa.Column("text_content", sa.Text, nullable=False),
        sa.Column("embedding", JSON, nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_embeddings_user_id", "embeddings", ["user_id"])
    op.create_index("ix_embeddings_source", "embeddings", ["source_type", "source_id"])


def downgrade() -> None:
    op.drop_table("embeddings")
    op.drop_table("tool_executions")
    op.drop_table("agent_logs")
    op.drop_table("emails")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS emailclassification")
    op.execute("DROP TYPE IF EXISTS emailstatus")
    op.execute("DROP EXTENSION IF EXISTS vector")
