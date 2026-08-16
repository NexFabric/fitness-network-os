"""Hashed one-time account invites (staff / member portal).

Revision ID: xd5e6f7a8b9c
Revises: xc4d5e6f7a8b
Create Date: 2026-08-16 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.rls import disable_rls, enable_rls

revision: str = "xd5e6f7a8b9c"
down_revision: str | Sequence[str] | None = "xc4d5e6f7a8b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account_invites",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "token_hash", name="uq_account_invites_tenant_token"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_account_invites_tenant_id"),
    )
    op.create_index(
        op.f("ix_account_invites_tenant_id"),
        "account_invites",
        ["tenant_id"],
        unique=False,
    )
    enable_rls("account_invites")


def downgrade() -> None:
    disable_rls("account_invites")
    op.drop_index(op.f("ix_account_invites_tenant_id"), table_name="account_invites")
    op.drop_table("account_invites")
