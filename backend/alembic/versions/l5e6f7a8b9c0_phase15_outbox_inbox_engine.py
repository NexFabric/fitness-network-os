"""Phase 15: outbox/inbox engine columns and tenant-scoped inbox uniqueness

Revision ID: l5e6f7a8b9c0
Revises: k4d5e6f7a8b9
Create Date: 2026-08-09 23:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "l5e6f7a8b9c0"
down_revision: str | Sequence[str] | None = "k4d5e6f7a8b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- outbox expand ---
    op.add_column(
        "outbox_events",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "outbox_events",
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "outbox_events",
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "outbox_events",
        sa.Column("aggregate_type", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "outbox_events",
        sa.Column("aggregate_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "outbox_events",
        sa.Column("dedupe_key", sa.String(length=255), nullable=True),
    )
    # NULL dedupe_key allowed multiple times (PG UNIQUE semantics)
    op.create_unique_constraint(
        "uq_outbox_events_tenant_dedupe",
        "outbox_events",
        ["tenant_id", "dedupe_key"],
    )
    op.create_index(
        "ix_outbox_events_available",
        "outbox_events",
        ["status", "available_at"],
        unique=False,
    )

    # --- inbox expand ---
    op.add_column(
        "inbox_events",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "inbox_events",
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Replace global unique event_id with tenant-scoped
    op.drop_index("ix_inbox_events_event_id", table_name="inbox_events")
    op.create_index(
        "ix_inbox_events_event_id", "inbox_events", ["event_id"], unique=False
    )
    op.create_unique_constraint(
        "uq_inbox_events_tenant_event_id",
        "inbox_events",
        ["tenant_id", "event_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_inbox_events_tenant_event_id", "inbox_events", type_="unique"
    )
    op.drop_index("ix_inbox_events_event_id", table_name="inbox_events")
    op.create_index(
        "ix_inbox_events_event_id", "inbox_events", ["event_id"], unique=True
    )
    op.drop_column("inbox_events", "processed_at")
    op.drop_column("inbox_events", "attempt_count")

    op.drop_index("ix_outbox_events_available", table_name="outbox_events")
    op.drop_constraint(
        "uq_outbox_events_tenant_dedupe", "outbox_events", type_="unique"
    )
    op.drop_column("outbox_events", "dedupe_key")
    op.drop_column("outbox_events", "aggregate_id")
    op.drop_column("outbox_events", "aggregate_type")
    op.drop_column("outbox_events", "processed_at")
    op.drop_column("outbox_events", "available_at")
    op.drop_column("outbox_events", "attempt_count")
