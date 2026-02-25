"""email templates table

Revision ID: 003_email_templates
Revises: 002_add_email_draft_fields
Create Date: 2026-02-19
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID

from alembic import op

revision: str = "003_email_templates"
down_revision: str | None = "002_user_preferences"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Email templates table
    op.create_table(
        "email_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("subject_template", sa.String(998), nullable=False),
        sa.Column("body_template", sa.Text, nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("variables", JSON, default=list),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_email_templates_user_id_category",
        "email_templates",
        ["user_id", "category"],
    )


def downgrade() -> None:
    op.drop_table("email_templates")
