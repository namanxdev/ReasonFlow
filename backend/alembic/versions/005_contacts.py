"""contacts table

Revision ID: 005_contacts
Revises: 004_idempotency_keys
Create Date: 2026-02-24
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from alembic import op

revision: str = "005_contacts"
down_revision: str | None = "004_idempotency_keys"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id", UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(256), nullable=True),
        sa.Column("company", sa.String(256), nullable=True),
        sa.Column("title", sa.String(256), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("tags", ARRAY(sa.String), nullable=True),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_contacts_user_id", "contacts", ["user_id"])
    op.create_index("ix_contacts_email", "contacts", ["email"])
    op.create_unique_constraint("uq_contacts_user_email", "contacts", ["user_id", "email"])


def downgrade() -> None:
    op.drop_table("contacts")
