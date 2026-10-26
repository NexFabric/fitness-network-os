"""Add Wave 2 membership models

Revision ID: c938894ffe0f
Revises: c938894ffe0e
Create Date: 2026-08-08 23:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.rls import disable_rls, enable_rls

# revision identifiers, used by Alembic.
revision: str = "c938894ffe0f"
down_revision: str | Sequence[str] | None = "c938894ffe0e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. plans
    op.create_table(
        "plans",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plans_tenant_id"), "plans", ["tenant_id"], unique=False)
    enable_rls("plans")

    # 2. plan_versions
    op.create_table(
        "plan_versions",
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("price_amount_minor", sa.Integer(), nullable=False),
        sa.Column("billing_cycle_months", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["plans.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_plan_versions_tenant_id"), "plan_versions", ["tenant_id"], unique=False
    )
    enable_rls("plan_versions")

    # 3. memberships
    op.create_table(
        "memberships",
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("plan_version_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
        ),
        sa.ForeignKeyConstraint(
            ["plan_version_id"],
            ["plan_versions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_memberships_tenant_id"), "memberships", ["tenant_id"], unique=False
    )
    enable_rls("memberships")

    # 4. entitlements
    op.create_table(
        "entitlements",
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=True),
        sa.Column("entitlement_type", sa.String(), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
        ),
        sa.ForeignKeyConstraint(
            ["membership_id"],
            ["memberships.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_entitlements_tenant_id"), "entitlements", ["tenant_id"], unique=False
    )
    enable_rls("entitlements")


def downgrade() -> None:
    disable_rls("entitlements")
    op.drop_index(op.f("ix_entitlements_tenant_id"), table_name="entitlements")
    op.drop_table("entitlements")

    disable_rls("memberships")
    op.drop_index(op.f("ix_memberships_tenant_id"), table_name="memberships")
    op.drop_table("memberships")

    disable_rls("plan_versions")
    op.drop_index(op.f("ix_plan_versions_tenant_id"), table_name="plan_versions")
    op.drop_table("plan_versions")

    disable_rls("plans")
    op.drop_index(op.f("ix_plans_tenant_id"), table_name="plans")
    op.drop_table("plans")
