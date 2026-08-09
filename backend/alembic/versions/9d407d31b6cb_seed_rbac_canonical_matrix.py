"""seed_rbac_canonical_matrix

Revision ID: 9d407d31b6cb
Revises: 45e716039e1c
Create Date: 2026-08-09 14:39:25.129415

"""
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9d407d31b6cb'
down_revision: str | Sequence[str] | None = '45e716039e1c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    from typing import Any
    # Hardcoded permissions dictionary (snapshot of permissions.yml)
    data: dict[str, Any] = {
        "roles": {
            "PLATFORM_SUPER_ADMIN": {
                "description": "Full access to entire platform",
                "permissions": ["*"]
            },
            "FEDERATION_ADMIN": {
                "description": "Full access to a specific federation and its gyms",
                "permissions": ["federation:read", "federation:write", "gym:read", "gym:write", "users:read", "users:write"]
            },
            "FEDERATION_ANALYST": {
                "description": "Read-only access to federation analytics",
                "permissions": ["federation:read", "gym:read"]
            },
            "FEDERATION_SUPPORT": {
                "description": "Support access for federation",
                "permissions": ["federation:read", "gym:read", "users:read"]
            },
            "GYM_OWNER": {
                "description": "Owner of a specific gym tenant",
                "permissions": ["gym:read", "gym:write", "memberships:read", "memberships:write", "checkins:read"]
            },
            "GYM_ADMIN": {
                "description": "Admin of a specific gym tenant",
                "permissions": ["gym:read", "gym:write", "memberships:read", "memberships:write", "checkins:read", "users:read", "users:write"]
            },
            "GYM_MANAGER": {
                "description": "Manager of a specific gym tenant",
                "permissions": ["gym:read", "memberships:read", "memberships:write", "checkins:read", "users:read"]
            },
            "ACCOUNTANT": {
                "description": "Accountant for a gym",
                "permissions": ["gym:read", "memberships:read"]
            },
            "FRONT_DESK": {
                "description": "Front desk staff",
                "permissions": ["gym:read", "memberships:read", "checkins:read", "checkins:write"]
            },
            "TRAINER": {
                "description": "Trainer in a gym",
                "permissions": ["gym:read", "memberships:read", "checkins:read"]
            },
            "MEMBER": {
                "description": "A standard gym member",
                "permissions": ["profile:read", "profile:write", "memberships:read", "checkins:read", "checkins:write"]
            }
        },
        "permissions": [
            {"id": "federation:read", "description": "Read federation details"},
            {"id": "federation:write", "description": "Modify federation details"},
            {"id": "gym:read", "description": "Read gym details"},
            {"id": "gym:write", "description": "Modify gym details"},
            {"id": "users:read", "description": "Read users in context"},
            {"id": "users:write", "description": "Modify users in context"},
            {"id": "memberships:read", "description": "Read memberships"},
            {"id": "memberships:write", "description": "Modify memberships"},
            {"id": "checkins:read", "description": "Read checkin history"},
            {"id": "checkins:write", "description": "Create checkins"},
            {"id": "profile:read", "description": "Read own profile"},
            {"id": "profile:write", "description": "Update own profile"},
            {"id": "*", "description": "Superuser wildcard"}
        ]
    }

    conn = op.get_bind()
    
    # 1. UPSERT Permissions
    permissions_list = data.get("permissions", [])
    if permissions_list:
        permissions_values = []
        for p in permissions_list:
            permissions_values.append({
                "id": str(uuid.uuid4()),
                "name": p["id"],
                "description": p.get("description", ""),
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            })
            
        stmt = sa.text("""
            INSERT INTO permissions (id, name, description, created_at, updated_at)
            VALUES (:id, :name, :description, :created_at, :updated_at)
            ON CONFLICT (name) DO UPDATE SET 
                description = EXCLUDED.description,
                updated_at = EXCLUDED.updated_at
        """)
        for pv in permissions_values:
            conn.execute(stmt, pv)

    # 2. UPSERT Roles
    roles_dict = data.get("roles", {})
    if roles_dict:
        roles_values = []
        for role_name, role_data in roles_dict.items():
            roles_values.append({
                "id": str(uuid.uuid4()),
                "name": role_name,
                "description": role_data.get("description", ""),
                "is_system": True,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            })
            
        stmt = sa.text("""
            INSERT INTO roles (id, name, description, is_system, created_at, updated_at)
            VALUES (:id, :name, :description, :is_system, :created_at, :updated_at)
            ON CONFLICT (name) DO UPDATE SET 
                description = EXCLUDED.description,
                is_system = EXCLUDED.is_system,
                updated_at = EXCLUDED.updated_at
        """)
        for rv in roles_values:
            conn.execute(stmt, rv)

    # 3. UPSERT Role-Permissions links
    if roles_dict:
        # Clear existing mappings for these roles to be safe
        for role_name in roles_dict:
            conn.execute(sa.text("""
                DELETE FROM role_permissions 
                WHERE role_id = (SELECT id FROM roles WHERE name = :name)
            """), {"name": role_name})

        # Insert new mappings
        for role_name, role_data in roles_dict.items():
            perms = role_data.get("permissions", [])
            for p in perms:
                conn.execute(sa.text("""
                    INSERT INTO role_permissions (role_id, permission_id)
                    SELECT r.id, p.id 
                    FROM roles r, permissions p 
                    WHERE r.name = :role_name AND p.name = :perm_name
                    ON CONFLICT DO NOTHING
                """), {"role_name": role_name, "perm_name": p})


def downgrade() -> None:
    """Downgrade schema."""
