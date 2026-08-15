"""seed access:override permission

Revision ID: x7a8b9c0d1e2
Revises: x6f7a8b9c0d1
Create Date: 2026-08-15 01:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "x7a8b9c0d1e2"
down_revision: str | None = "x6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Insert permission if missing
    conn.execute(
        sa.text(
            """
            INSERT INTO permissions (id, name, description, created_at, updated_at)
            VALUES (gen_random_uuid(), 'access:override', 'Manual turnstile check-in override for reception and staff', now(), now())
            ON CONFLICT (name) DO NOTHING;
            """
        )
    )

    # 2. Grant to GYM_OWNER, GYM_ADMIN, GYM_MANAGER, FRONT_DESK, and PLATFORM_SUPER_ADMIN
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            CROSS JOIN permissions p
            WHERE r.name IN ('GYM_OWNER', 'GYM_ADMIN', 'GYM_MANAGER', 'FRONT_DESK', 'PLATFORM_SUPER_ADMIN')
              AND p.name = 'access:override'
            ON CONFLICT DO NOTHING;
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE permission_id IN (SELECT id FROM permissions WHERE name = 'access:override');
            
            DELETE FROM permissions WHERE name = 'access:override';
            """
        )
    )
