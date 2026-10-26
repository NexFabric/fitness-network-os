"""Data retention policies.

Revision ID: x3c4d5e6f7a8
Revises: x2b3c4d5e6f7
Create Date: 2026-08-14 21:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.rls import disable_rls, enable_rls

revision: str = "x3c4d5e6f7a8"
down_revision: str | Sequence[str] | None = "x2b3c4d5e6f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "data_retention_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("data_category", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "retention_days",
            sa.Integer(),
            nullable=True,
            comment="NULL = indefinite retention (requires legal basis)",
        ),
        sa.Column(
            "deletion_method",
            sa.String(length=20),
            server_default="ANONYMIZE",
            nullable=False,
        ),
        sa.Column("legal_basis", sa.String(length=255), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "requires_legal_review",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
            comment="True = retention_days must be set by legal/business, not engineering",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_data_retention_policies_tenant_id"
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "data_category",
            name="uq_data_retention_policies_tenant_category",
        ),
        sa.CheckConstraint(
            "deletion_method IN ('DELETE', 'ANONYMIZE', 'ARCHIVE')",
            name="ck_retention_policies_deletion_method",
        ),
        sa.CheckConstraint(
            "retention_days IS NULL OR retention_days > 0",
            name="ck_retention_policies_days_positive",
        ),
    )

    op.create_index(
        op.f("ix_data_retention_policies_tenant_id"),
        "data_retention_policies",
        ["tenant_id"],
        unique=False,
    )

    enable_rls("data_retention_policies")


def downgrade() -> None:
    disable_rls("data_retention_policies")
    op.drop_index(
        op.f("ix_data_retention_policies_tenant_id"),
        table_name="data_retention_policies",
    )
    op.drop_table("data_retention_policies")
