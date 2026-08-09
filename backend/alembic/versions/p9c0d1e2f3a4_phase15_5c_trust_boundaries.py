"""Phase 15.5C: trust boundary RBAC — outbox/inbox + MEMBER self perms

- Revoke outbox:write|read and inbox:write|read from GYM_OWNER/ADMIN/MANAGER
- MEMBER loses tenant-wide memberships/checkins/entitlements perms
- MEMBER gains *:self variants for self-service /me routes

Revision ID: p9c0d1e2f3a4
Revises: o8b9c0d1e2f3
Create Date: 2026-08-09 26:00:00.000000

"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision: str = "p9c0d1e2f3a4"
down_revision: str | Sequence[str] | None = "o8b9c0d1e2f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_PERMISSIONS = [
    ("memberships:read:self", "Read own memberships via /me (bound member)"),
    ("checkins:read:self", "Read own checkins via /me (bound member)"),
    ("checkins:write:self", "Create own checkins via /me (bound member)"),
    ("entitlements:read:self", "Read own entitlements via /me (bound member)"),
    ("entitlements:check:self", "Check own entitlement via /me (bound member)"),
]

ROLE_GRANTS_ADD: dict[str, list[str]] = {
    "MEMBER": [
        "memberships:read:self",
        "checkins:read:self",
        "checkins:write:self",
        "entitlements:read:self",
        "entitlements:check:self",
    ],
}

ROLE_GRANTS_REVOKE: dict[str, list[str]] = {
    "MEMBER": [
        "memberships:read",
        "checkins:read",
        "checkins:write",
        "entitlements:read",
        "entitlements:check",
    ],
    "GYM_OWNER": [
        "outbox:write",
        "outbox:read",
        "inbox:write",
        "inbox:read",
    ],
    "GYM_ADMIN": [
        "outbox:write",
        "outbox:read",
        "inbox:write",
        "inbox:read",
    ],
    "GYM_MANAGER": [
        "outbox:write",
        "outbox:read",
        "inbox:write",
        "inbox:read",
    ],
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

    for role_name, perms in ROLE_GRANTS_ADD.items():
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

    for role_name, perms in ROLE_GRANTS_REVOKE.items():
        for perm_name in perms:
            conn.execute(
                sa.text(
                    """
                    DELETE FROM role_permissions
                    WHERE role_id = (SELECT id FROM roles WHERE name = :role_name)
                      AND permission_id = (
                          SELECT id FROM permissions WHERE name = :perm_name
                      )
                    """
                ),
                {"role_name": role_name, "perm_name": perm_name},
            )


def downgrade() -> None:
    conn = op.get_bind()

    for role_name, perms in ROLE_GRANTS_REVOKE.items():
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

    for role_name, perms in ROLE_GRANTS_ADD.items():
        for perm_name in perms:
            conn.execute(
                sa.text(
                    """
                    DELETE FROM role_permissions
                    WHERE role_id = (SELECT id FROM roles WHERE name = :role_name)
                      AND permission_id = (
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
