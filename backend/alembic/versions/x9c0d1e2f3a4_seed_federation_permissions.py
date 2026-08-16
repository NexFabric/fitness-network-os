"""seed federation compliance alerts and passport permissions

Revision ID: x9c0d1e2f3a4
Revises: x8b9c0d1e2f3
Create Date: 2026-08-15 17:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "x9c0d1e2f3a4"
down_revision: str | None = "x8b9c0d1e2f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Insert permissions if missing
    conn.execute(
        sa.text(
            """
            INSERT INTO permissions (id, name, description, created_at, updated_at)
            VALUES 
                (gen_random_uuid(), 'compliance:read', 'Read compliance records and certification audits', now(), now()),
                (gen_random_uuid(), 'compliance:write', 'Create and update compliance audit records', now(), now()),
                (gen_random_uuid(), 'alerts:broadcast', 'Broadcast network-wide alerts to federation clubs', now(), now()),
                (gen_random_uuid(), 'passport:manage', 'Configure cross-club passport and roaming rules', now(), now())
            ON CONFLICT (name) DO NOTHING;
            """
        )
    )

    # 2. Grant to FEDERATION_ADMIN and PLATFORM_SUPER_ADMIN
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            CROSS JOIN permissions p
            WHERE r.name IN ('FEDERATION_ADMIN', 'PLATFORM_SUPER_ADMIN')
              AND p.name IN ('compliance:read', 'compliance:write', 'alerts:broadcast', 'passport:manage')
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
            WHERE permission_id IN (
                SELECT id FROM permissions WHERE name IN ('compliance:read', 'compliance:write', 'alerts:broadcast', 'passport:manage')
            );
            
            DELETE FROM permissions 
            WHERE name IN ('compliance:read', 'compliance:write', 'alerts:broadcast', 'passport:manage');
            """
        )
    )
