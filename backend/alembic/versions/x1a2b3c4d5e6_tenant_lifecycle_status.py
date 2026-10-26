"""Tenant lifecycle status.

Revision ID: x1a2b3c4d5e6
Revises: w6d7e8f9a0b1
Create Date: 2026-08-14 21:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "x1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "w6d7e8f9a0b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add new columns to tenants table
    op.add_column(
        "tenants",
        sa.Column(
            "status", sa.String(length=20), server_default="ACTIVE", nullable=False
        ),
    )
    op.add_column(
        "tenants", sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "tenants", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("tenants", sa.Column("suspension_reason", sa.Text(), nullable=True))
    op.add_column("tenants", sa.Column("closure_reason", sa.Text(), nullable=True))

    # Add Check Constraint
    op.create_check_constraint(
        "ck_tenants_status", "tenants", "status IN ('ACTIVE', 'SUSPENDED', 'CLOSED')"
    )


def downgrade() -> None:
    op.drop_constraint("ck_tenants_status", "tenants", type_="check")
    op.drop_column("tenants", "closure_reason")
    op.drop_column("tenants", "suspension_reason")
    op.drop_column("tenants", "closed_at")
    op.drop_column("tenants", "suspended_at")
    op.drop_column("tenants", "status")
