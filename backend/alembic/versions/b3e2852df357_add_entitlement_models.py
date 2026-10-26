"""Add entitlement models with RLS

Revision ID: b3e2852df357
Revises: 62afa7f4b3b1
Create Date: 2026-08-09 18:30:51.798299

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.rls import disable_rls, enable_rls

# revision identifiers, used by Alembic.
revision: str = "b3e2852df357"
down_revision: str | Sequence[str] | None = "62afa7f4b3b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "entitlement_definitions",
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "type",
            sa.Enum("COUNT", "BOOLEAN", name="entitlementtype"),
            nullable=False,
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_entitlement_definitions_tenant_id"
        ),
    )
    op.create_index(
        "ix_entitlement_def_tenant_code",
        "entitlement_definitions",
        ["tenant_id", "code"],
        unique=True,
    )
    op.create_index(
        op.f("ix_entitlement_definitions_tenant_id"),
        "entitlement_definitions",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "plan_entitlements",
        sa.Column("plan_version_id", sa.Uuid(), nullable=False),
        sa.Column("entitlement_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "unlimited", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "quantity >= 0", name="ck_plan_entitlements_quantity_nonneg"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "entitlement_id"],
            ["entitlement_definitions.tenant_id", "entitlement_definitions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "plan_version_id"],
            ["plan_versions.tenant_id", "plan_versions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_plan_entitlements_tenant_id"),
    )
    op.create_index(
        "ix_plan_entit_tenant_pv_entit",
        "plan_entitlements",
        ["tenant_id", "plan_version_id", "entitlement_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_plan_entitlements_tenant_id"),
        "plan_entitlements",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "membership_entitlements",
        sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column("entitlement_id", sa.Uuid(), nullable=False),
        sa.Column("source_plan_version_id", sa.Uuid(), nullable=True),
        sa.Column("granted_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "unlimited", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="ACTIVE"),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "granted_quantity >= 0", name="ck_membership_entitlements_granted_nonneg"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "entitlement_id"],
            ["entitlement_definitions.tenant_id", "entitlement_definitions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_plan_version_id"],
            ["plan_versions.tenant_id", "plan_versions.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_membership_entitlements_tenant_id"
        ),
    )
    op.create_index(
        "ix_memb_entit_tenant_memb_entit",
        "membership_entitlements",
        ["tenant_id", "membership_id", "entitlement_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_membership_entitlements_tenant_id"),
        "membership_entitlements",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "entitlement_wallets",
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column("membership_entitlement_id", sa.Uuid(), nullable=False),
        sa.Column("entitlement_id", sa.Uuid(), nullable=False),
        sa.Column("allocated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consumed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("remaining", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "allocated >= 0", name="ck_entitlement_wallets_allocated_nonneg"
        ),
        sa.CheckConstraint(
            "reserved >= 0", name="ck_entitlement_wallets_reserved_nonneg"
        ),
        sa.CheckConstraint(
            "consumed >= 0", name="ck_entitlement_wallets_consumed_nonneg"
        ),
        sa.CheckConstraint(
            "remaining >= 0", name="ck_entitlement_wallets_remaining_nonneg"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "entitlement_id"],
            ["entitlement_definitions.tenant_id", "entitlement_definitions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "member_id"],
            ["members.tenant_id", "members.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "membership_entitlement_id"],
            ["membership_entitlements.tenant_id", "membership_entitlements.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_entitlement_wallets_tenant_id"),
    )
    op.create_index(
        "ix_entit_wallets_tenant_me",
        "entitlement_wallets",
        ["tenant_id", "membership_entitlement_id"],
        unique=True,
    )
    op.create_index(
        "ix_entit_wallets_tenant_memb_entit",
        "entitlement_wallets",
        ["tenant_id", "membership_id", "entitlement_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_entitlement_wallets_tenant_id"),
        "entitlement_wallets",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "entitlement_transactions",
        sa.Column("wallet_id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=True),
        sa.Column("entitlement_id", sa.Uuid(), nullable=True),
        sa.Column("transaction_type", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("balance_before", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("balance_after", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "wallet_id"],
            ["entitlement_wallets.tenant_id", "entitlement_wallets.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_entitlement_transactions_tenant_id"
        ),
    )
    op.create_index(
        "ix_entit_tx_tenant_idem_key",
        "entitlement_transactions",
        ["tenant_id", "idempotency_key"],
        unique=True,
    )
    op.create_index(
        "ix_entit_tx_tenant_wallet",
        "entitlement_transactions",
        ["tenant_id", "wallet_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_entitlement_transactions_tenant_id"),
        "entitlement_transactions",
        ["tenant_id"],
        unique=False,
    )

    enable_rls("entitlement_definitions")
    enable_rls("plan_entitlements")
    enable_rls("membership_entitlements")
    enable_rls("entitlement_wallets")
    enable_rls("entitlement_transactions")


def downgrade() -> None:
    disable_rls("entitlement_transactions")
    disable_rls("entitlement_wallets")
    disable_rls("membership_entitlements")
    disable_rls("plan_entitlements")
    disable_rls("entitlement_definitions")

    op.drop_index(
        op.f("ix_entitlement_transactions_tenant_id"),
        table_name="entitlement_transactions",
    )
    op.drop_index("ix_entit_tx_tenant_wallet", table_name="entitlement_transactions")
    op.drop_index("ix_entit_tx_tenant_idem_key", table_name="entitlement_transactions")
    op.drop_table("entitlement_transactions")

    op.drop_index(
        op.f("ix_entitlement_wallets_tenant_id"), table_name="entitlement_wallets"
    )
    op.drop_index(
        "ix_entit_wallets_tenant_memb_entit", table_name="entitlement_wallets"
    )
    op.drop_index("ix_entit_wallets_tenant_me", table_name="entitlement_wallets")
    op.drop_table("entitlement_wallets")

    op.drop_index(
        op.f("ix_membership_entitlements_tenant_id"),
        table_name="membership_entitlements",
    )
    op.drop_index(
        "ix_memb_entit_tenant_memb_entit", table_name="membership_entitlements"
    )
    op.drop_table("membership_entitlements")

    op.drop_index(
        op.f("ix_plan_entitlements_tenant_id"), table_name="plan_entitlements"
    )
    op.drop_index("ix_plan_entit_tenant_pv_entit", table_name="plan_entitlements")
    op.drop_table("plan_entitlements")

    op.drop_index(
        op.f("ix_entitlement_definitions_tenant_id"),
        table_name="entitlement_definitions",
    )
    op.drop_index(
        "ix_entitlement_def_tenant_code", table_name="entitlement_definitions"
    )
    op.drop_table("entitlement_definitions")

    op.execute("DROP TYPE IF EXISTS entitlementtype")
