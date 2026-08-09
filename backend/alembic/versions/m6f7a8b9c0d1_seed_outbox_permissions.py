"""seed outbox/inbox permissions

Revision ID: m6f7a8b9c0d1
Revises: l5e6f7a8b9c0
Create Date: 2026-08-09 23:35:00.000000

"""
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision: str = "m6f7a8b9c0d1"
down_revision: str | Sequence[str] | None = "l5e6f7a8b9c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_PERMISSIONS = [
    ("outbox:write", "Enqueue outbox events"),
    ("outbox:dispatch", "Dispatch claimed outbox events"),
    ("outbox:read", "Read outbox status"),
    ("inbox:write", "Receive inbox events"),
    ("inbox:read", "Read inbox status"),
]

ROLE_GRANTS: dict[str, list[str]] = {
    "GYM_OWNER": [
        "outbox:write",
        "outbox:dispatch",
        "outbox:read",
        "inbox:write",
        "inbox:read",
    ],
    "GYM_ADMIN": [
        "outbox:write",
        "outbox:dispatch",
        "outbox:read",
        "inbox:write",
        "inbox:read",
    ],
    "GYM_MANAGER": ["outbox:write", "outbox:read", "inbox:write", "inbox:read"],
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
    for name, _ in NEW_PERMISSIONS:
        conn.execute(
            sa.text(
                """
                DELETE FROM role_permissions
                WHERE permission_id IN (SELECT id FROM permissions WHERE name = :name)
                """
            ),
            {"name": name},
        )
        conn.execute(
            sa.text("DELETE FROM permissions WHERE name = :name"),
            {"name": name},
        )
