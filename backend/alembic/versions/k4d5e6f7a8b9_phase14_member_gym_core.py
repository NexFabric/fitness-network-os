"""Phase 14: member_number uniqueness, staff user uniqueness, permissions

Revision ID: k4d5e6f7a8b9
Revises: j3c4d5e6f7a8
Create Date: 2026-08-09 23:00:00.000000

"""
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision: str = "k4d5e6f7a8b9"
down_revision: str | Sequence[str] | None = "j3c4d5e6f7a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_PERMISSIONS = [
    ("members:read", "Read member profiles"),
    ("members:write", "Create and update members"),
    ("locations:read", "Read gym locations/branches"),
    ("locations:write", "Create and update locations"),
    ("staff:read", "Read staff links"),
    ("staff:write", "Link users as staff"),
]

ROLE_GRANTS: dict[str, list[str]] = {
    "GYM_OWNER": [
        "members:read",
        "members:write",
        "locations:read",
        "locations:write",
        "staff:read",
        "staff:write",
    ],
    "GYM_ADMIN": [
        "members:read",
        "members:write",
        "locations:read",
        "locations:write",
        "staff:read",
        "staff:write",
    ],
    "GYM_MANAGER": [
        "members:read",
        "members:write",
        "locations:read",
        "staff:read",
    ],
    "FRONT_DESK": ["members:read", "members:write", "locations:read"],
    "TRAINER": ["members:read", "locations:read"],
    "MEMBER": ["members:read"],
}


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_members_tenant_member_number", "members", ["tenant_id", "member_number"]
    )
    op.create_unique_constraint(
        "uq_staff_tenant_user", "staff", ["tenant_id", "user_id"]
    )

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

    op.drop_constraint("uq_staff_tenant_user", "staff", type_="unique")
    op.drop_constraint("uq_members_tenant_member_number", "members", type_="unique")
