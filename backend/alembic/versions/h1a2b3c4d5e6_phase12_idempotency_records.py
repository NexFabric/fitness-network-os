"""Phase 12: idempotency_records table

Revision ID: h1a2b3c4d5e6
Revises: f7a8b9c0d1e2
Create Date: 2026-08-09 22:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.rls import disable_rls, enable_rls

revision: str = "h1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "f7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Ensure legacy table exists for deprecated IdempotencyKey model (was model-only).
    op.create_table(
        "idempotency_keys",
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("request_path", sa.String(length=255), nullable=False),
        sa.Column("request_params", sa.JSON(), nullable=True),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.JSON(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_idempotency_keys_tenant_id"),
    )
    # unique=True on model column creates this index (not a separate named UQ)
    op.create_index("ix_idempotency_keys_key", "idempotency_keys", ["key"], unique=True)
    op.create_index(
        op.f("ix_idempotency_keys_tenant_id"),
        "idempotency_keys",
        ["tenant_id"],
        unique=False,
    )
    enable_rls("idempotency_keys")

    op.create_table(
        "idempotency_records",
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("operation", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default="PROCESSING",
        ),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.JSON(), nullable=True),
        sa.Column("resource_type", sa.String(), nullable=True),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_token", sa.String(length=64), nullable=True),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_idempotency_records_tenant_id"
        ),
    )
    op.create_index(
        "ix_idempotency_records_tenant_op_key",
        "idempotency_records",
        ["tenant_id", "operation", "key"],
        unique=True,
    )
    op.create_index(
        "ix_idempotency_records_tenant_expires",
        "idempotency_records",
        ["tenant_id", "expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_idempotency_records_tenant_id"),
        "idempotency_records",
        ["tenant_id"],
        unique=False,
    )
    enable_rls("idempotency_records")


def downgrade() -> None:
    disable_rls("idempotency_records")
    op.drop_index(
        op.f("ix_idempotency_records_tenant_id"),
        table_name="idempotency_records",
    )
    op.drop_index(
        "ix_idempotency_records_tenant_expires",
        table_name="idempotency_records",
    )
    op.drop_index(
        "ix_idempotency_records_tenant_op_key",
        table_name="idempotency_records",
    )
    op.drop_table("idempotency_records")

    disable_rls("idempotency_keys")
    op.drop_index(op.f("ix_idempotency_keys_tenant_id"), table_name="idempotency_keys")
    op.drop_index("ix_idempotency_keys_key", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
