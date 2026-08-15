"""Phase 15.5B: RBAC least-privilege + members.user_id binding

- MEMBER loses members:read and access:issue; gains access:issue:self
- Tenant roles lose outbox:dispatch (platform/worker only)
- members.user_id nullable FK + unique (tenant_id, user_id)

Revision ID: o8b9c0d1e2f3
Revises: n7a8b9c0d1e2
Create Date: 2026-08-09 24:10:00.000000

"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision: str = "o8b9c0d1e2f3"
down_revision: str | Sequence[str] | None = "n7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_PERMISSIONS = [
    (
        "access:issue:self",
        "Issue short-lived QR access credentials for own bound member profile",
    ),
]

# Grants to add (must match permissions.yml)
ROLE_GRANTS_ADD: dict[str, list[str]] = {
    "MEMBER": ["access:issue:self"],
}

# Explicit revokes for least privilege (do NOT re-grant members:read to MEMBER)
ROLE_GRANTS_REVOKE: dict[str, list[str]] = {
    "MEMBER": ["members:read", "access:issue"],
    "GYM_OWNER": ["outbox:dispatch"],
    "GYM_ADMIN": ["outbox:dispatch"],
    "GYM_MANAGER": ["outbox:dispatch"],
}


def upgrade() -> None:
    # --- members.user_id binding ---
    op.add_column(
        "members",
        sa.Column("user_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        op.f("ix_members_user_id"),
        "members",
        ["user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_members_user_id_users",
        "members",
        "users",
        ["user_id"],
        ["id"],
    )
    # Partial unique: at most one member per (tenant, user) when bound
    op.create_index(
        "uq_members_tenant_user",
        "members",
        ["tenant_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
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

    # Also strip outbox:dispatch from any remaining roles (exact YAML parity)
    conn.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE permission_id = (
                SELECT id FROM permissions WHERE name = 'outbox:dispatch'
            )
            """
        )
    )

    # --- Finance: immutable allocations + append-only reversals ---
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION deny_payment_allocation_mutation()
            RETURNS trigger AS $$
            BEGIN
              RAISE EXCEPTION 'payment_allocations is immutable';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )
    op.execute(
        sa.text(
            "DROP TRIGGER IF EXISTS trg_deny_payment_allocation_update "
            "ON payment_allocations"
        )
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_deny_payment_allocation_update "
            "BEFORE UPDATE ON payment_allocations "
            "FOR EACH ROW EXECUTE PROCEDURE deny_payment_allocation_mutation()"
        )
    )
    op.execute(
        sa.text(
            "DROP TRIGGER IF EXISTS trg_deny_payment_allocation_delete "
            "ON payment_allocations"
        )
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_deny_payment_allocation_delete "
            "BEFORE DELETE ON payment_allocations "
            "FOR EACH ROW EXECUTE PROCEDURE deny_payment_allocation_mutation()"
        )
    )
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION deny_payment_allocation_reversal_mutation()
            RETURNS trigger AS $$
            BEGIN
              RAISE EXCEPTION 'payment_allocation_reversals is append-only';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )
    op.execute(
        sa.text(
            "DROP TRIGGER IF EXISTS trg_deny_payment_allocation_reversal_update "
            "ON payment_allocation_reversals"
        )
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_deny_payment_allocation_reversal_update "
            "BEFORE UPDATE ON payment_allocation_reversals "
            "FOR EACH ROW EXECUTE PROCEDURE deny_payment_allocation_reversal_mutation()"
        )
    )
    op.execute(
        sa.text(
            "DROP TRIGGER IF EXISTS trg_deny_payment_allocation_reversal_delete "
            "ON payment_allocation_reversals"
        )
    )
    op.execute(
        sa.text(
            "CREATE TRIGGER trg_deny_payment_allocation_reversal_delete "
            "BEFORE DELETE ON payment_allocation_reversals "
            "FOR EACH ROW EXECUTE PROCEDURE deny_payment_allocation_reversal_mutation()"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DROP TRIGGER IF EXISTS trg_deny_payment_allocation_reversal_delete "
            "ON payment_allocation_reversals"
        )
    )
    op.execute(
        sa.text(
            "DROP TRIGGER IF EXISTS trg_deny_payment_allocation_reversal_update "
            "ON payment_allocation_reversals"
        )
    )
    op.execute(
        sa.text("DROP FUNCTION IF EXISTS deny_payment_allocation_reversal_mutation()")
    )
    op.execute(
        sa.text(
            "DROP TRIGGER IF EXISTS trg_deny_payment_allocation_delete "
            "ON payment_allocations"
        )
    )
    op.execute(
        sa.text(
            "DROP TRIGGER IF EXISTS trg_deny_payment_allocation_update "
            "ON payment_allocations"
        )
    )
    op.execute(sa.text("DROP FUNCTION IF EXISTS deny_payment_allocation_mutation()"))

    conn = op.get_bind()

    # Best-effort reverse of grants (re-apply previous over-privileges for rollback only)
    for role_name, perms in ROLE_GRANTS_REVOKE.items():
        for perm_name in perms:
            # Skip re-granting if permission was never seeded (e.g. outbox on manager)
            conn.execute(
                sa.text(
                    """
                    INSERT INTO role_permissions (role_id, permission_id)
                    SELECT r.id, p.id
                    FROM roles r, permissions p
                    WHERE r.name = :role_name AND p.name = :perm_name
                    AND p.id IS NOT NULL
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

    op.drop_index("uq_members_tenant_user", table_name="members")
    op.drop_constraint("fk_members_user_id_users", "members", type_="foreignkey")
    op.drop_index(op.f("ix_members_user_id"), table_name="members")
    op.drop_column("members", "user_id")
