"""update rbac models

Revision ID: 0a561fd73793
Revises: db8f4db0e58d
Create Date: 2026-08-09 12:11:52.418823

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.rls import disable_rls, enable_rls

# revision identifiers, used by Alembic.
revision: str = '0a561fd73793'
down_revision: str | Sequence[str] | None = '261bdee314d7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('user_roles', sa.Column('organization_id', sa.Uuid(), nullable=True))
    op.alter_column('user_roles', 'tenant_id',
               existing_type=sa.UUID(),
               nullable=True)
    op.drop_constraint('uq_user_roles_tenant_id', 'user_roles', type_='unique')
    op.create_index(op.f('ix_user_roles_organization_id'), 'user_roles', ['organization_id'], unique=False)
    op.drop_constraint('fk_user_roles_tenants', 'user_roles', type_='foreignkey')
    op.create_foreign_key('fk_user_roles_tenants', 'user_roles', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_user_roles_organizations', 'user_roles', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    disable_rls('user_roles')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    enable_rls('user_roles')
    op.drop_constraint('fk_user_roles_organizations', 'user_roles', type_='foreignkey')
    op.drop_constraint('fk_user_roles_tenants', 'user_roles', type_='foreignkey')
    op.create_foreign_key('fk_user_roles_tenants', 'user_roles', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.drop_index(op.f('ix_user_roles_organization_id'), table_name='user_roles')
    op.create_unique_constraint('uq_user_roles_tenant_id', 'user_roles', ['tenant_id', 'id'])
    op.alter_column('user_roles', 'tenant_id',
               existing_type=sa.UUID(),
               nullable=False)
    op.drop_column('user_roles', 'organization_id')
    # ### end Alembic commands ###
