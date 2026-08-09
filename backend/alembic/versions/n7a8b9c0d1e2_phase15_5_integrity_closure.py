"""Phase 15.5: integrity closure — outbox lease, inbox retry, allocation reversals, ledger

Revision ID: n7a8b9c0d1e2
Revises: m6f7a8b9c0d1
Create Date: 2026-08-09 23:50:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.rls import disable_rls, enable_rls

revision: str = "n7a8b9c0d1e2"
down_revision: str | Sequence[str] | None = "m6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- outbox lease ---
    op.add_column(
        "outbox_events",
        sa.Column("worker_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "outbox_events",
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_outbox_events_lease",
        "outbox_events",
        ["status", "lease_until"],
        unique=False,
    )

    # --- inbox retry ---
    op.add_column(
        "inbox_events",
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_inbox_events_available",
        "inbox_events",
        ["status", "available_at"],
        unique=False,
    )
    op.execute(
        "UPDATE inbox_events SET available_at = created_at WHERE available_at IS NULL"
    )

    # --- payment allocation reversals ---
    op.create_table(
        "payment_allocation_reversals",
        sa.Column("allocation_id", sa.Uuid(), nullable=False),
        sa.Column("refund_id", sa.Uuid(), nullable=True),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "amount_minor > 0", name="ck_payment_allocation_reversals_amount_pos"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "allocation_id"],
            ["payment_allocations.tenant_id", "payment_allocations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "refund_id"],
            ["refunds.tenant_id", "refunds.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_payment_allocation_reversals_tenant_id"
        ),
    )
    op.create_index(
        "ix_payment_allocation_reversals_allocation_id",
        "payment_allocation_reversals",
        ["allocation_id"],
        unique=False,
    )
    op.create_index(
        "ix_payment_allocation_reversals_refund_id",
        "payment_allocation_reversals",
        ["refund_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_allocation_reversals_tenant_id"),
        "payment_allocation_reversals",
        ["tenant_id"],
        unique=False,
    )
    enable_rls("payment_allocation_reversals")

    # --- entitlement_transactions: RESTRICT wallet delete ---
    op.drop_constraint(
        "entitlement_transactions_tenant_id_wallet_id_fkey",
        "entitlement_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "entitlement_transactions_tenant_id_wallet_id_fkey",
        "entitlement_transactions",
        "entitlement_wallets",
        ["tenant_id", "wallet_id"],
        ["tenant_id", "id"],
        ondelete="RESTRICT",
    )

    # Append-only ledger triggers
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION deny_entitlement_tx_mutation()
            RETURNS trigger AS $$
            BEGIN
              RAISE EXCEPTION 'entitlement_transactions is append-only';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )
    op.execute(
        sa.text(
            "DROP TRIGGER IF EXISTS trg_deny_entitlement_tx_update "
            "ON entitlement_transactions"
        )
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_deny_entitlement_tx_update "
            "BEFORE UPDATE ON entitlement_transactions "
            "FOR EACH ROW EXECUTE PROCEDURE deny_entitlement_tx_mutation()"
        )
    )
    op.execute(
        sa.text(
            "DROP TRIGGER IF EXISTS trg_deny_entitlement_tx_delete "
            "ON entitlement_transactions"
        )
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_deny_entitlement_tx_delete "
            "BEFORE DELETE ON entitlement_transactions "
            "FOR EACH ROW EXECUTE PROCEDURE deny_entitlement_tx_mutation()"
        )
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS trg_deny_entitlement_tx_delete ON entitlement_transactions"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_deny_entitlement_tx_update ON entitlement_transactions"
    )
    op.execute("DROP FUNCTION IF EXISTS deny_entitlement_tx_mutation()")

    op.drop_constraint(
        "entitlement_transactions_tenant_id_wallet_id_fkey",
        "entitlement_transactions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "entitlement_transactions_tenant_id_wallet_id_fkey",
        "entitlement_transactions",
        "entitlement_wallets",
        ["tenant_id", "wallet_id"],
        ["tenant_id", "id"],
        ondelete="CASCADE",
    )

    disable_rls("payment_allocation_reversals")
    op.drop_index(
        op.f("ix_payment_allocation_reversals_tenant_id"),
        table_name="payment_allocation_reversals",
    )
    op.drop_index(
        "ix_payment_allocation_reversals_refund_id",
        table_name="payment_allocation_reversals",
    )
    op.drop_index(
        "ix_payment_allocation_reversals_allocation_id",
        table_name="payment_allocation_reversals",
    )
    op.drop_table("payment_allocation_reversals")

    op.drop_index("ix_inbox_events_available", table_name="inbox_events")
    op.drop_column("inbox_events", "available_at")

    op.drop_index("ix_outbox_events_lease", table_name="outbox_events")
    op.drop_column("outbox_events", "lease_until")
    op.drop_column("outbox_events", "worker_id")
