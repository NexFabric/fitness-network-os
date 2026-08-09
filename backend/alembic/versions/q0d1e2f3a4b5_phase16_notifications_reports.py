"""Phase 16: expand notification + report domain columns + RBAC seed

Revision ID: q0d1e2f3a4b5
Revises: p9c0d1e2f3a4
Create Date: 2026-08-10 00:00:00.000000

"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision: str = "q0d1e2f3a4b5"
down_revision: str | Sequence[str] | None = "p9c0d1e2f3a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_PERMISSIONS = [
    ("notifications:read", "Read notification templates and deliveries"),
    ("notifications:write", "Create and manage notification templates"),
    ("notifications:send", "Schedule notification deliveries"),
    ("reports:read", "Read report definitions and runs"),
    ("reports:write", "Create and manage report definitions"),
    ("reports:run", "Request report runs"),
]

ROLE_GRANTS: dict[str, list[str]] = {
    "GYM_OWNER": [
        "notifications:read",
        "notifications:write",
        "notifications:send",
        "reports:read",
        "reports:write",
        "reports:run",
    ],
    "GYM_ADMIN": [
        "notifications:read",
        "notifications:write",
        "notifications:send",
        "reports:read",
        "reports:write",
        "reports:run",
    ],
    "GYM_MANAGER": [
        "notifications:read",
        "notifications:send",
        "reports:read",
        "reports:run",
    ],
    "ACCOUNTANT": ["reports:read"],
    "FRONT_DESK": ["notifications:read", "notifications:send"],
}


def upgrade() -> None:
    # --- notification_templates ---
    op.add_column(
        "notification_templates",
        sa.Column(
            "code",
            sa.String(length=100),
            nullable=False,
            server_default="default",
        ),
    )
    op.execute(
        sa.text(
            """
            UPDATE notification_templates
            SET code = 'tmpl_' || replace(id::text, '-', '')
            WHERE code = 'default'
            """
        )
    )
    op.alter_column("notification_templates", "code", server_default=None)
    op.add_column(
        "notification_templates",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "notification_templates",
        sa.Column("locale", sa.String(length=16), nullable=True),
    )
    op.create_unique_constraint(
        "uq_notification_templates_tenant_code",
        "notification_templates",
        ["tenant_id", "code"],
    )
    op.create_index(
        "ix_notification_templates_channel",
        "notification_templates",
        ["tenant_id", "channel"],
        unique=False,
    )

    # --- notification_deliveries ---
    op.alter_column(
        "notification_deliveries",
        "recipient_user_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("recipient_address", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("subject", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("body", sa.Text(), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column(
            "context",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("dedupe_key", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("provider", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("source_event_type", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("source_event_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("correlation_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_notification_deliveries_status",
        "notification_deliveries",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_notification_deliveries_available",
        "notification_deliveries",
        ["status", "available_at"],
        unique=False,
    )
    op.create_index(
        "uq_notification_deliveries_tenant_dedupe",
        "notification_deliveries",
        ["tenant_id", "dedupe_key"],
        unique=True,
        postgresql_where=sa.text("dedupe_key IS NOT NULL"),
    )

    # --- report_definitions ---
    op.add_column(
        "report_definitions",
        sa.Column(
            "code",
            sa.String(length=100),
            nullable=False,
            server_default="default",
        ),
    )
    op.execute(
        sa.text(
            """
            UPDATE report_definitions
            SET code = 'rpt_' || replace(id::text, '-', '')
            WHERE code = 'default'
            """
        )
    )
    op.alter_column("report_definitions", "code", server_default=None)
    op.add_column(
        "report_definitions",
        sa.Column(
            "report_type",
            sa.String(length=100),
            nullable=False,
            server_default="GENERIC",
        ),
    )
    op.add_column(
        "report_definitions",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.create_unique_constraint(
        "uq_report_definitions_tenant_code",
        "report_definitions",
        ["tenant_id", "code"],
    )

    # --- report_runs ---
    op.add_column(
        "report_runs",
        sa.Column("export_format", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "report_runs",
        sa.Column("row_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "report_runs",
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "report_runs",
        sa.Column("dedupe_key", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "report_runs",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "report_runs",
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_report_runs_status",
        "report_runs",
        ["tenant_id", "status"],
        unique=False,
    )
    op.create_index(
        "uq_report_runs_tenant_dedupe",
        "report_runs",
        ["tenant_id", "dedupe_key"],
        unique=True,
        postgresql_where=sa.text("dedupe_key IS NOT NULL"),
    )

    # --- RBAC seed (YAML is source of truth; DB must match for check_permissions_db) ---
    conn = op.get_bind()
    now = datetime.now(UTC)
    for name, description in NEW_PERMISSIONS:
        exists = conn.execute(
            sa.text("SELECT id FROM permissions WHERE name = :name"),
            {"name": name},
        ).fetchone()
        if not exists:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO permissions (id, name, description, created_at, updated_at)
                    VALUES (:id, :name, :description, :created_at, :updated_at)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "description": description,
                    "created_at": now,
                    "updated_at": now,
                },
            )

    for role_name, perms in ROLE_GRANTS.items():
        for perm_name in perms:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO role_permissions (role_id, permission_id)
                    SELECT r.id, p.id
                    FROM roles r, permissions p
                    WHERE r.name = :role_name AND p.name = :perm_name
                    AND NOT EXISTS (
                        SELECT 1 FROM role_permissions rp
                        WHERE rp.role_id = r.id AND rp.permission_id = p.id
                    )
                    """
                ),
                {"role_name": role_name, "perm_name": perm_name},
            )


def downgrade() -> None:
    conn = op.get_bind()
    for role_name, perms in ROLE_GRANTS.items():
        for perm_name in perms:
            conn.execute(
                sa.text(
                    """
                    DELETE FROM role_permissions
                    WHERE role_id IN (SELECT id FROM roles WHERE name = :role_name)
                      AND permission_id IN (
                          SELECT id FROM permissions WHERE name = :perm_name
                      )
                    """
                ),
                {"role_name": role_name, "perm_name": perm_name},
            )
    for name, _ in NEW_PERMISSIONS:
        conn.execute(
            sa.text("DELETE FROM permissions WHERE name = :name"),
            {"name": name},
        )

    op.drop_index(
        "uq_report_runs_tenant_dedupe",
        table_name="report_runs",
        postgresql_where=sa.text("dedupe_key IS NOT NULL"),
    )
    op.drop_index("ix_report_runs_status", table_name="report_runs")
    op.drop_column("report_runs", "finished_at")
    op.drop_column("report_runs", "started_at")
    op.drop_column("report_runs", "dedupe_key")
    op.drop_column("report_runs", "requested_by_user_id")
    op.drop_column("report_runs", "row_count")
    op.drop_column("report_runs", "export_format")

    op.drop_constraint(
        "uq_report_definitions_tenant_code",
        "report_definitions",
        type_="unique",
    )
    op.drop_column("report_definitions", "is_active")
    op.drop_column("report_definitions", "report_type")
    op.drop_column("report_definitions", "code")

    op.drop_index(
        "uq_notification_deliveries_tenant_dedupe",
        table_name="notification_deliveries",
        postgresql_where=sa.text("dedupe_key IS NOT NULL"),
    )
    op.drop_index(
        "ix_notification_deliveries_available",
        table_name="notification_deliveries",
    )
    op.drop_index(
        "ix_notification_deliveries_status",
        table_name="notification_deliveries",
    )
    op.drop_column("notification_deliveries", "correlation_id")
    op.drop_column("notification_deliveries", "source_event_id")
    op.drop_column("notification_deliveries", "source_event_type")
    op.drop_column("notification_deliveries", "provider_message_id")
    op.drop_column("notification_deliveries", "provider")
    op.drop_column("notification_deliveries", "dedupe_key")
    op.drop_column("notification_deliveries", "sent_at")
    op.drop_column("notification_deliveries", "available_at")
    op.drop_column("notification_deliveries", "attempt_count")
    op.drop_column("notification_deliveries", "context")
    op.drop_column("notification_deliveries", "body")
    op.drop_column("notification_deliveries", "subject")
    op.drop_column("notification_deliveries", "recipient_address")
    op.alter_column(
        "notification_deliveries",
        "recipient_user_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )

    op.drop_index(
        "ix_notification_templates_channel",
        table_name="notification_templates",
    )
    op.drop_constraint(
        "uq_notification_templates_tenant_code",
        "notification_templates",
        type_="unique",
    )
    op.drop_column("notification_templates", "locale")
    op.drop_column("notification_templates", "is_active")
    op.drop_column("notification_templates", "code")
