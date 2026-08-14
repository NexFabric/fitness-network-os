"""seed finance:read:self permission

Revision ID: x4d5e6f7a8b9
Revises: x3c4d5e6f7a8
Create Date: 2026-08-14 23:23:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "x4d5e6f7a8b9"
down_revision: Union[str, None] = "x3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # 1. Insert permission if missing
    conn.execute(
        sa.text(
            """
            INSERT INTO permissions (id, name, description, created_at, updated_at)
            VALUES (gen_random_uuid(), 'finance:read:self', 'Read own invoices and payment history via /me (bound member)', now(), now())
            ON CONFLICT (name) DO NOTHING;
            """
        )
    )
    
    # 2. Grant to MEMBER and PLATFORM_SUPER_ADMIN
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            CROSS JOIN permissions p
            WHERE r.name IN ('MEMBER', 'PLATFORM_SUPER_ADMIN')
              AND p.name = 'finance:read:self'
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
            WHERE permission_id IN (SELECT id FROM permissions WHERE name = 'finance:read:self');
            
            DELETE FROM permissions WHERE name = 'finance:read:self';
            """
        )
    )
