"""KVKK DSAR request ledger.

Revision ID: xe6f7a8b9c0d
Revises: xd5e6f7a8b9c
Create Date: 2026-08-16 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.rls import disable_rls, enable_rls

revision: str = "xe6f7a8b9c0d"
down_revision: str | Sequence[str] | None = "xd5e6f7a8b9c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dsar_requests",
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("package_uri", sa.String(length=1024), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("dedupe_key", sa.String(length=128), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "member_id"],
            ["members.tenant_id", "members.id"],
            name="fk_dsar_requests_member_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_dsar_requests_tenant_id"),
    )
    op.create_index(
        op.f("ix_dsar_requests_tenant_id"), "dsar_requests", ["tenant_id"], unique=False
    )
    op.create_index(
        "ix_dsar_requests_tenant_dedupe",
        "dsar_requests",
        ["tenant_id", "dedupe_key"],
        unique=True,
        postgresql_where=sa.text("dedupe_key IS NOT NULL"),
    )
    enable_rls("dsar_requests")


def downgrade() -> None:
    disable_rls("dsar_requests")
    op.drop_index("ix_dsar_requests_tenant_dedupe", table_name="dsar_requests")
    op.drop_index(op.f("ix_dsar_requests_tenant_id"), table_name="dsar_requests")
    op.drop_table("dsar_requests")
