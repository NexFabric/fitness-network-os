"""add federation models

Revision ID: 32bea30c0ed8
Revises: 8d4b31a89f92
Create Date: 2026-08-09 00:03:21.977408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.db.rls import enable_rls, disable_rls


# revision identifiers, used by Alembic.
revision: str = '32bea30c0ed8'
down_revision: Union[str, Sequence[str], None] = '8d4b31a89f92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('compliance_records',
    sa.Column('certification_name', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('audit_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('auditor_notes', sa.String(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('tenant_id', sa.Uuid(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_records_tenant_id'), 'compliance_records', ['tenant_id'], unique=False)
    op.create_table('passport_configs',
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('allowed_home_gym_tiers', sa.String(), nullable=True),
    sa.Column('rules', sa.JSON(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('tenant_id', sa.Uuid(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_passport_configs_tenant_id'), 'passport_configs', ['tenant_id'], unique=False)
    op.create_table('network_alerts',
    sa.Column('organization_id', sa.Uuid(), nullable=False),
    sa.Column('target_tenant_id', sa.Uuid(), nullable=True),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('message', sa.String(), nullable=False),
    sa.Column('severity', sa.String(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['target_tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    enable_rls('compliance_records')
    enable_rls('passport_configs')


def downgrade() -> None:
    """Downgrade schema."""
    disable_rls('passport_configs')
    disable_rls('compliance_records')
    
    op.drop_table('network_alerts')
    op.drop_index(op.f('ix_passport_configs_tenant_id'), table_name='passport_configs')
    op.drop_table('passport_configs')
    op.drop_index(op.f('ix_compliance_records_tenant_id'), table_name='compliance_records')
    op.drop_table('compliance_records')
