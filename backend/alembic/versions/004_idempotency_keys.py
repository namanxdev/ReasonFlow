"""idempotency keys table

Revision ID: 004_idempotency_keys
Revises: 003_email_templates
Create Date: 2026-02-22
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004_idempotency_keys"
down_revision: str | None = "003_email_templates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("key", sa.String(255), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("idempotency_keys")
