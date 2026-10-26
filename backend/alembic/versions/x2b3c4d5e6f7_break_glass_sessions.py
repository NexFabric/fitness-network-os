"""Break glass sessions.

Revision ID: x2b3c4d5e6f7
Revises: x1a2b3c4d5e6
Create Date: 2026-08-14 21:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "x2b3c4d5e6f7"
down_revision: str | Sequence[str] | None = "x1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "break_glass_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("target_tenant_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("ticket_reference", sa.String(length=255), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default="ACTIVE", nullable=False
        ),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actions_taken", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'EXPIRED', 'REVOKED')",
            name="ck_break_glass_sessions_status",
        ),
    )

    op.create_index(
        op.f("ix_break_glass_sessions_actor_id"),
        "break_glass_sessions",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_break_glass_sessions_target_tenant_id"),
        "break_glass_sessions",
        ["target_tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_break_glass_active",
        "break_glass_sessions",
        ["status", "expires_at"],
        unique=False,
    )

    # Seed permission
    op.execute(
        """
        INSERT INTO permissions (id, name, description, created_at, updated_at) 
        VALUES (gen_random_uuid(), 'admin:break_glass', 'Emergency tenant access', now(), now())
        ON CONFLICT (name) DO NOTHING;
        """
    )
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id) 
        SELECT r.id, p.id FROM roles r, permissions p 
        WHERE r.name = 'PLATFORM_SUPER_ADMIN' AND p.name = 'admin:break_glass'
        ON CONFLICT DO NOTHING;
        """
    )


def downgrade() -> None:
    # Remove seeded permissions
    op.execute(
        """
        DELETE FROM role_permissions 
        WHERE permission_id IN (SELECT id FROM permissions WHERE name = 'admin:break_glass');
        """
    )
    op.execute("DELETE FROM permissions WHERE name = 'admin:break_glass';")

    op.drop_index("ix_break_glass_active", table_name="break_glass_sessions")
    op.drop_index(
        op.f("ix_break_glass_sessions_target_tenant_id"),
        table_name="break_glass_sessions",
    )
    op.drop_index(
        op.f("ix_break_glass_sessions_actor_id"), table_name="break_glass_sessions"
    )
    op.drop_table("break_glass_sessions")
