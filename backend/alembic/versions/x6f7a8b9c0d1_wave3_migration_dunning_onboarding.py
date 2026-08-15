"""wave 3 data import, payment attempts, dunning, and tenant onboarding

Revision ID: x6f7a8b9c0d1
Revises: x5e6f7a8b9c0
Create Date: 2026-08-15 00:02:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "x6f7a8b9c0d1"
down_revision: str | None = "x5e6f7a8b9c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def enable_rls(table_name: str) -> None:
    op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
    op.execute(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;")
    op.execute(
        f"""
        CREATE POLICY {table_name}_tenant_isolation_policy ON {table_name}
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
        """
    )


def disable_rls(table_name: str) -> None:
    op.execute(
        f"DROP POLICY IF EXISTS {table_name}_tenant_isolation_policy ON {table_name};"
    )
    op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;")


def upgrade() -> None:
    # 1. Invoice retry columns
    op.add_column(
        "invoices",
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "invoices",
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. Data Import Batches & Rows
    op.create_table(
        "data_import_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column(
            "status", sa.String(length=32), server_default="PREVIEW", nullable=False
        ),
        sa.Column("total_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("valid_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("invalid_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("imported_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
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
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_data_import_batches_tenant_id_id"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    enable_rls("data_import_batches")

    op.create_table(
        "data_import_rows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column(
            "status", sa.String(length=32), server_default="VALID", nullable=False
        ),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "parsed_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["data_import_batches.tenant_id", "data_import_batches.id"],
        ),
    )
    enable_rls("data_import_rows")

    # 3. Payment Attempts & Dunning Policies
    op.create_table(
        "payment_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("invoice_id", sa.Uuid(), nullable=False),
        sa.Column("billing_account_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), server_default="TRY", nullable=False
        ),
        sa.Column(
            "status", sa.String(length=20), server_default="PENDING", nullable=False
        ),
        sa.Column("gateway_provider", sa.String(length=64), nullable=True),
        sa.Column("gateway_attempt_ref", sa.String(length=128), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "invoice_id"], ["invoices.tenant_id", "invoices.id"]
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "billing_account_id"],
            ["billing_accounts.tenant_id", "billing_accounts.id"],
        ),
    )
    enable_rls("payment_attempts")

    op.create_table(
        "dunning_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column(
            "name",
            sa.String(length=100),
            server_default="Default Dunning",
            nullable=False,
        ),
        sa.Column(
            "grace_period_days", sa.Integer(), server_default="3", nullable=False
        ),
        sa.Column(
            "max_retry_attempts", sa.Integer(), server_default="3", nullable=False
        ),
        sa.Column(
            "retry_interval_days", sa.Integer(), server_default="2", nullable=False
        ),
        sa.Column(
            "block_access_on_failure",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    enable_rls("dunning_policies")

    # 4. Tenant Onboardings
    op.create_table(
        "tenant_onboardings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column(
            "current_stage",
            sa.String(length=32),
            server_default="ORG_CREATED",
            nullable=False,
        ),
        sa.Column(
            "step_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("is_completed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    enable_rls("tenant_onboardings")


def downgrade() -> None:
    disable_rls("tenant_onboardings")
    op.drop_table("tenant_onboardings")

    disable_rls("dunning_policies")
    op.drop_table("dunning_policies")

    disable_rls("payment_attempts")
    op.drop_table("payment_attempts")

    disable_rls("data_import_rows")
    op.drop_table("data_import_rows")

    disable_rls("data_import_batches")
    op.drop_table("data_import_batches")

    op.drop_column("invoices", "next_retry_at")
    op.drop_column("invoices", "retry_count")
