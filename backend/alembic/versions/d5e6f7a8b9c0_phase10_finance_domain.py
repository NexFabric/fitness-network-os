"""Phase 10 finance domain completion

Revision ID: d5e6f7a8b9c0
Revises: c4f9a1b2e3d0
Create Date: 2026-08-09 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.rls import disable_rls, enable_rls

revision: str = "d5e6f7a8b9c0"
down_revision: str | Sequence[str] | None = "c4f9a1b2e3d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Extend billing_accounts ---
    op.add_column(
        "billing_accounts",
        sa.Column(
            "currency", sa.String(length=3), nullable=False, server_default="TRY"
        ),
    )
    op.add_column(
        "billing_accounts",
        sa.Column("status", sa.String(), nullable=False, server_default="ACTIVE"),
    )
    op.create_index(
        "ix_billing_accounts_tenant_member",
        "billing_accounts",
        ["tenant_id", "member_id"],
        unique=True,
        postgresql_where=sa.text("member_id IS NOT NULL"),
    )

    # --- Extend invoices ---
    op.add_column("invoices", sa.Column("membership_id", sa.Uuid(), nullable=True))
    op.add_column(
        "invoices", sa.Column("invoice_number", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "invoices", sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "invoices", sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "invoices",
        sa.Column(
            "paid_amount_minor", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "invoices",
        sa.Column(
            "discount_amount_minor", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "invoices", sa.Column("idempotency_key", sa.String(length=128), nullable=True)
    )
    op.create_foreign_key(
        "fk_invoices_membership_tenant",
        "invoices",
        "memberships",
        ["tenant_id", "membership_id"],
        ["tenant_id", "id"],
    )
    op.create_index("ix_invoices_membership_id", "invoices", ["membership_id"])
    op.create_index(
        "ix_invoices_tenant_idem",
        "invoices",
        ["tenant_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.create_index(
        "ix_invoices_tenant_number",
        "invoices",
        ["tenant_id", "invoice_number"],
        unique=True,
        postgresql_where=sa.text("invoice_number IS NOT NULL"),
    )
    op.create_check_constraint(
        "ck_invoices_total_nonneg", "invoices", "total_amount_minor >= 0"
    )
    op.create_check_constraint(
        "ck_invoices_paid_nonneg", "invoices", "paid_amount_minor >= 0"
    )
    op.create_check_constraint(
        "ck_invoices_discount_nonneg", "invoices", "discount_amount_minor >= 0"
    )
    op.create_check_constraint(
        "ck_invoices_paid_lte_total",
        "invoices",
        "paid_amount_minor <= total_amount_minor",
    )

    # --- Extend invoice_items ---
    op.add_column(
        "invoice_items",
        sa.Column(
            "unit_amount_minor", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "invoice_items", sa.Column("source_type", sa.String(length=64), nullable=True)
    )
    op.add_column("invoice_items", sa.Column("source_id", sa.Uuid(), nullable=True))
    op.execute(
        "UPDATE invoice_items SET unit_amount_minor = amount_minor WHERE quantity = 1"
    )
    op.create_check_constraint(
        "ck_invoice_items_qty_pos", "invoice_items", "quantity > 0"
    )
    op.create_check_constraint(
        "ck_invoice_items_amount_nonneg", "invoice_items", "amount_minor >= 0"
    )
    op.create_check_constraint(
        "ck_invoice_items_unit_nonneg", "invoice_items", "unit_amount_minor >= 0"
    )

    # --- Extend payments ---
    op.add_column(
        "payments",
        sa.Column(
            "refunded_amount_minor", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "payments", sa.Column("provider", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "payments", sa.Column("provider_ref", sa.String(length=128), nullable=True)
    )
    op.add_column(
        "payments", sa.Column("idempotency_key", sa.String(length=128), nullable=True)
    )
    op.add_column(
        "payments", sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        "ix_payments_tenant_idem",
        "payments",
        ["tenant_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.create_check_constraint("ck_payments_amount_pos", "payments", "amount_minor > 0")
    op.create_check_constraint(
        "ck_payments_refunded_nonneg", "payments", "refunded_amount_minor >= 0"
    )
    op.create_check_constraint(
        "ck_payments_refunded_lte_amount",
        "payments",
        "refunded_amount_minor <= amount_minor",
    )

    op.create_check_constraint(
        "ck_payment_allocations_amount_pos",
        "payment_allocations",
        "amount_minor > 0",
    )

    # --- New tables ---
    op.create_table(
        "refunds",
        sa.Column("payment_id", sa.Uuid(), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_minor > 0", name="ck_refunds_amount_pos"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "payment_id"],
            ["payments.tenant_id", "payments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_refunds_tenant_id"),
    )
    op.create_index("ix_refunds_payment_id", "refunds", ["payment_id"])
    op.create_index("ix_refunds_tenant_id", "refunds", ["tenant_id"])
    op.create_index(
        "ix_refunds_tenant_idem",
        "refunds",
        ["tenant_id", "idempotency_key"],
        unique=True,
    )

    op.create_table(
        "credit_notes",
        sa.Column("billing_account_id", sa.Uuid(), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("remaining_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_minor > 0", name="ck_credit_notes_amount_pos"),
        sa.CheckConstraint(
            "remaining_minor >= 0", name="ck_credit_notes_remaining_nonneg"
        ),
        sa.CheckConstraint(
            "remaining_minor <= amount_minor",
            name="ck_credit_notes_remaining_lte_amount",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "billing_account_id"],
            ["billing_accounts.tenant_id", "billing_accounts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_credit_notes_tenant_id"),
    )
    op.create_index(
        "ix_credit_notes_billing_account_id", "credit_notes", ["billing_account_id"]
    )
    op.create_index("ix_credit_notes_tenant_id", "credit_notes", ["tenant_id"])
    op.create_index(
        "ix_credit_notes_tenant_idem",
        "credit_notes",
        ["tenant_id", "idempotency_key"],
        unique=True,
    )

    op.create_table(
        "credit_applications",
        sa.Column("credit_note_id", sa.Uuid(), nullable=False),
        sa.Column("invoice_id", sa.Uuid(), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "amount_minor > 0", name="ck_credit_applications_amount_pos"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "credit_note_id"],
            ["credit_notes.tenant_id", "credit_notes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "invoice_id"],
            ["invoices.tenant_id", "invoices.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_credit_applications_tenant_id"),
    )
    op.create_index(
        "ix_credit_applications_credit_note_id",
        "credit_applications",
        ["credit_note_id"],
    )
    op.create_index(
        "ix_credit_applications_invoice_id", "credit_applications", ["invoice_id"]
    )
    op.create_index(
        "ix_credit_applications_tenant_id", "credit_applications", ["tenant_id"]
    )

    op.create_table(
        "discounts",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=True),
        sa.Column("percent_bps", sa.Integer(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(amount_minor IS NOT NULL AND percent_bps IS NULL) OR "
            "(amount_minor IS NULL AND percent_bps IS NOT NULL)",
            name="ck_discounts_fixed_or_percent",
        ),
        sa.CheckConstraint(
            "amount_minor IS NULL OR amount_minor >= 0",
            name="ck_discounts_amount_nonneg",
        ),
        sa.CheckConstraint(
            "percent_bps IS NULL OR (percent_bps >= 0 AND percent_bps <= 10000)",
            name="ck_discounts_percent_bps_range",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_discounts_tenant_id"),
    )
    op.create_index(
        "ix_discounts_tenant_code", "discounts", ["tenant_id", "code"], unique=True
    )
    op.create_index("ix_discounts_tenant_id", "discounts", ["tenant_id"])

    op.create_table(
        "invoice_discounts",
        sa.Column("invoice_id", sa.Uuid(), nullable=False),
        sa.Column("discount_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_minor > 0", name="ck_invoice_discounts_amount_pos"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "invoice_id"],
            ["invoices.tenant_id", "invoices.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "discount_id"],
            ["discounts.tenant_id", "discounts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_invoice_discounts_tenant_id"),
    )
    op.create_index(
        "ix_invoice_discounts_invoice_id", "invoice_discounts", ["invoice_id"]
    )
    op.create_index(
        "ix_invoice_discounts_tenant_id", "invoice_discounts", ["tenant_id"]
    )

    op.create_table(
        "reconciliation_runs",
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_reconciliation_runs_tenant_id"),
    )
    op.create_index(
        "ix_reconciliation_runs_tenant_id", "reconciliation_runs", ["tenant_id"]
    )

    op.create_table(
        "reconciliation_items",
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("external_ref", sa.String(length=128), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("matched_payment_id", sa.Uuid(), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_minor != 0", name="ck_recon_items_amount_nonzero"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "run_id"],
            ["reconciliation_runs.tenant_id", "reconciliation_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "matched_payment_id"],
            ["payments.tenant_id", "payments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_reconciliation_items_tenant_id"
        ),
    )
    op.create_index(
        "ix_reconciliation_items_run_id", "reconciliation_items", ["run_id"]
    )
    op.create_index(
        "ix_reconciliation_items_tenant_id", "reconciliation_items", ["tenant_id"]
    )

    enable_rls("refunds")
    enable_rls("credit_notes")
    enable_rls("credit_applications")
    enable_rls("discounts")
    enable_rls("invoice_discounts")
    enable_rls("reconciliation_runs")
    enable_rls("reconciliation_items")


def downgrade() -> None:
    for table in (
        "reconciliation_items",
        "reconciliation_runs",
        "invoice_discounts",
        "discounts",
        "credit_applications",
        "credit_notes",
        "refunds",
    ):
        disable_rls(table)

    op.drop_table("reconciliation_items")
    op.drop_table("reconciliation_runs")
    op.drop_table("invoice_discounts")
    op.drop_table("discounts")
    op.drop_table("credit_applications")
    op.drop_table("credit_notes")
    op.drop_table("refunds")

    op.drop_constraint("ck_payment_allocations_amount_pos", "payment_allocations")
    op.drop_constraint("ck_payments_refunded_lte_amount", "payments")
    op.drop_constraint("ck_payments_refunded_nonneg", "payments")
    op.drop_constraint("ck_payments_amount_pos", "payments")
    op.drop_index("ix_payments_tenant_idem", table_name="payments")
    op.drop_column("payments", "paid_at")
    op.drop_column("payments", "idempotency_key")
    op.drop_column("payments", "provider_ref")
    op.drop_column("payments", "provider")
    op.drop_column("payments", "refunded_amount_minor")

    op.drop_constraint("ck_invoice_items_unit_nonneg", "invoice_items")
    op.drop_constraint("ck_invoice_items_amount_nonneg", "invoice_items")
    op.drop_constraint("ck_invoice_items_qty_pos", "invoice_items")
    op.drop_column("invoice_items", "source_id")
    op.drop_column("invoice_items", "source_type")
    op.drop_column("invoice_items", "unit_amount_minor")

    op.drop_constraint("ck_invoices_paid_lte_total", "invoices")
    op.drop_constraint("ck_invoices_discount_nonneg", "invoices")
    op.drop_constraint("ck_invoices_paid_nonneg", "invoices")
    op.drop_constraint("ck_invoices_total_nonneg", "invoices")
    op.drop_index("ix_invoices_tenant_number", table_name="invoices")
    op.drop_index("ix_invoices_tenant_idem", table_name="invoices")
    op.drop_index("ix_invoices_membership_id", table_name="invoices")
    op.drop_constraint("fk_invoices_membership_tenant", "invoices", type_="foreignkey")
    op.drop_column("invoices", "idempotency_key")
    op.drop_column("invoices", "discount_amount_minor")
    op.drop_column("invoices", "paid_amount_minor")
    op.drop_column("invoices", "voided_at")
    op.drop_column("invoices", "issued_at")
    op.drop_column("invoices", "invoice_number")
    op.drop_column("invoices", "membership_id")

    op.drop_index("ix_billing_accounts_tenant_member", table_name="billing_accounts")
    op.drop_column("billing_accounts", "status")
    op.drop_column("billing_accounts", "currency")
