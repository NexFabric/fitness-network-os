"""Deduplicate user_roles and add partial unique grants.

Revision ID: xg8b9c0d1e2f
Revises: xf7a8b9c0d1e
Create Date: 2026-08-16 16:00:00.000000

A user may hold a given role at most once per tenant, per organization, or
globally. PostgreSQL treats NULL as distinct, so one btree unique is not
enough — three partial indexes cover the three scopes.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "xg8b9c0d1e2f"
down_revision: str | Sequence[str] | None = "xf7a8b9c0d1e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM user_roles a
        USING user_roles b
        WHERE a.id > b.id
          AND a.user_id = b.user_id
          AND a.role_id = b.role_id
          AND a.tenant_id IS NOT NULL
          AND a.tenant_id = b.tenant_id
        """
    )
    op.execute(
        """
        DELETE FROM user_roles a
        USING user_roles b
        WHERE a.id > b.id
          AND a.user_id = b.user_id
          AND a.role_id = b.role_id
          AND a.organization_id IS NOT NULL
          AND a.organization_id = b.organization_id
        """
    )
    op.execute(
        """
        DELETE FROM user_roles a
        USING user_roles b
        WHERE a.id > b.id
          AND a.user_id = b.user_id
          AND a.role_id = b.role_id
          AND a.tenant_id IS NULL
          AND b.tenant_id IS NULL
          AND a.organization_id IS NULL
          AND b.organization_id IS NULL
        """
    )
    op.create_index(
        "uq_user_roles_user_role_tenant",
        "user_roles",
        ["user_id", "role_id", "tenant_id"],
        unique=True,
        postgresql_where=sa.text("tenant_id IS NOT NULL"),
        if_not_exists=True,
    )
    op.create_index(
        "uq_user_roles_user_role_org",
        "user_roles",
        ["user_id", "role_id", "organization_id"],
        unique=True,
        postgresql_where=sa.text("organization_id IS NOT NULL"),
        if_not_exists=True,
    )
    op.create_index(
        "uq_user_roles_user_role_global",
        "user_roles",
        ["user_id", "role_id"],
        unique=True,
        postgresql_where=sa.text("tenant_id IS NULL AND organization_id IS NULL"),
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_user_roles_user_role_global",
        table_name="user_roles",
        if_exists=True,
    )
    op.drop_index(
        "uq_user_roles_user_role_org",
        table_name="user_roles",
        if_exists=True,
    )
    op.drop_index(
        "uq_user_roles_user_role_tenant",
        table_name="user_roles",
        if_exists=True,
    )
