"""seed reception:read permission for front-desk staff

TRAINER keeps members:read (assignment-scoped member APIs) but must not open
the reception workspace, which returns tenant-wide PII and billing.

Revision ID: xb3c4d5e6f7a
Revises: xa2b3c4d5e6f
Create Date: 2026-08-15 23:00:00.000000

"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision: str = "xb3c4d5e6f7a"
down_revision: str | Sequence[str] | None = "xa2b3c4d5e6f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_PERMISSIONS = [
    (
        "reception:read",
        "Search and open the front-desk reception workspace (not assignment-scoped trainers)",
    ),
]

ROLE_GRANTS: dict[str, list[str]] = {
    "GYM_OWNER": ["reception:read"],
    "GYM_ADMIN": ["reception:read"],
    "GYM_MANAGER": ["reception:read"],
    "FRONT_DESK": ["reception:read"],
}


def upgrade() -> None:
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
