"""trainer_assignments table + members:read:all permission

Gives Scope.ASSIGNED real data behind it. TRAINER keeps ``members:read`` (so it
may still call the member endpoints) but is deliberately NOT granted
``members:read:all``, which is what narrows its row scope to assigned members.

Revision ID: s2f3a4b5c6d7
Revises: r1e2f3a4b5c6
Create Date: 2026-08-11 00:30:00.000000

"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op
from app.db.rls import disable_rls, enable_rls

revision: str = "s2f3a4b5c6d7"
down_revision: str | Sequence[str] | None = "r1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_PERMISSIONS = [
    (
        "members:read:all",
        "See every member in the tenant; without it a reader sees only assigned members",
    ),
]

ROLE_GRANTS: dict[str, list[str]] = {
    "GYM_OWNER": ["members:read:all"],
    "GYM_ADMIN": ["members:read:all"],
    "GYM_MANAGER": ["members:read:all"],
    "FRONT_DESK": ["members:read:all"],
    # TRAINER intentionally omitted — assignment-scoped by design.
}


def upgrade() -> None:
    op.create_table(
        "trainer_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("trainer_user_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["trainer_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "member_id"], ["members.tenant_id", "members.id"]
        ),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_trainer_assignments_tenant_id"
        ),
    )
    op.create_index(
        "ix_trainer_assignments_tenant_id", "trainer_assignments", ["tenant_id"]
    )
    op.create_index(
        "ix_trainer_assignments_trainer_user_id",
        "trainer_assignments",
        ["trainer_user_id"],
    )
    op.create_index(
        "ix_trainer_assignments_member_id", "trainer_assignments", ["member_id"]
    )
    op.create_index(
        "ix_trainer_assignments_tenant_trainer",
        "trainer_assignments",
        ["tenant_id", "trainer_user_id"],
    )
    # Only one live link per (tenant, trainer, member); revoked rows persist.
    op.create_index(
        "uq_trainer_assignments_active",
        "trainer_assignments",
        ["tenant_id", "trainer_user_id", "member_id"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )

    enable_rls("trainer_assignments")

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
    for perms in ROLE_GRANTS.values():
        for perm_name in perms:
            conn.execute(
                sa.text(
                    """
                    DELETE FROM role_permissions
                    WHERE permission_id IN (
                        SELECT id FROM permissions WHERE name = :perm_name
                    )
                    """
                ),
                {"perm_name": perm_name},
            )
    for name, _ in NEW_PERMISSIONS:
        conn.execute(
            sa.text("DELETE FROM permissions WHERE name = :name"),
            {"name": name},
        )

    disable_rls("trainer_assignments")
    op.drop_table("trainer_assignments")
