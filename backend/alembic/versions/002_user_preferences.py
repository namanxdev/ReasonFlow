"""user preferences table

Revision ID: 002_user_preferences
Revises: 001_initial
Create Date: 2026-02-19
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID

from alembic import op

revision: str = "002_user_preferences"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "auto_approval_threshold",
            sa.Float,
            nullable=False,
            server_default="0.9",
        ),
        sa.Column(
            "email_sync_frequency_minutes",
            sa.Integer,
            nullable=False,
            server_default="15",
        ),
        sa.Column(
            "notification_settings",
            JSON,
            nullable=False,
            server_default='{}',
        ),
        sa.Column(
            "timezone",
            sa.String(100),
            nullable=False,
            server_default="UTC",
        ),
        sa.Column(
            "daily_digest_enabled",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "auto_classify_on_sync",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "max_auto_responses_per_day",
            sa.Integer,
            nullable=False,
            server_default="50",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_preferences")
