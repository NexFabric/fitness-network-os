"""Add access models

Revision ID: a1b2c3d4e5f6
Revises: dd603a516953
Create Date: 2026-08-08 23:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from app.db.rls import enable_rls, disable_rls

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'dd603a516953'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # key_status_enum
    sa.Enum('ACTIVE', 'VERIFY_ONLY', 'REVOKED', name='key_status_enum').create(op.get_bind())
    
    # device_status_enum
    sa.Enum('ONLINE', 'DEGRADED', 'OFFLINE', 'CLOCK_DRIFT', 'SYNC_PENDING', 'CERTIFICATE_EXPIRING', name='device_status_enum').create(op.get_bind())
    
    # access_status_enum
    sa.Enum('GRANTED', 'DENIED', name='access_status_enum').create(op.get_bind())
    
    op.create_table('signing_keys',
    sa.Column('kid', sa.String(), nullable=False),
    sa.Column('status', postgresql.ENUM('ACTIVE', 'VERIFY_ONLY', 'REVOKED', name='key_status_enum', create_type=False), nullable=False),
    sa.Column('key_material', sa.Text(), nullable=False),
    sa.Column('tenant_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_signing_keys_kid'), 'signing_keys', ['kid'], unique=True)
    op.create_index(op.f('ix_signing_keys_tenant_id'), 'signing_keys', ['tenant_id'], unique=False)
    enable_rls('signing_keys')

    op.create_table('devices',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('location_id', sa.Uuid(), nullable=False),
    sa.Column('capabilities', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('status', postgresql.ENUM('ONLINE', 'DEGRADED', 'OFFLINE', 'CLOCK_DRIFT', 'SYNC_PENDING', 'CERTIFICATE_EXPIRING', name='device_status_enum', create_type=False), nullable=False),
    sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_devices_location_id'), 'devices', ['location_id'], unique=False)
    op.create_index(op.f('ix_devices_tenant_id'), 'devices', ['tenant_id'], unique=False)
    enable_rls('devices')

    op.create_table('access_attempts',
    sa.Column('member_id', sa.Uuid(), nullable=True),
    sa.Column('device_id', sa.Uuid(), nullable=True),
    sa.Column('status', postgresql.ENUM('GRANTED', 'DENIED', name='access_status_enum', create_type=False), nullable=False),
    sa.Column('denial_reason', sa.String(), nullable=True),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.Column('tenant_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
    sa.ForeignKeyConstraint(['member_id'], ['members.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_access_attempts_device_id'), 'access_attempts', ['device_id'], unique=False)
    op.create_index(op.f('ix_access_attempts_member_id'), 'access_attempts', ['member_id'], unique=False)
    op.create_index(op.f('ix_access_attempts_tenant_id'), 'access_attempts', ['tenant_id'], unique=False)
    enable_rls('access_attempts')

    op.create_table('checkins',
    sa.Column('member_id', sa.Uuid(), nullable=False),
    sa.Column('location_id', sa.Uuid(), nullable=False),
    sa.Column('device_id', sa.Uuid(), nullable=True),
    sa.Column('checkin_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('checkout_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
    sa.ForeignKeyConstraint(['member_id'], ['members.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checkins_device_id'), 'checkins', ['device_id'], unique=False)
    op.create_index(op.f('ix_checkins_location_id'), 'checkins', ['location_id'], unique=False)
    op.create_index(op.f('ix_checkins_member_id'), 'checkins', ['member_id'], unique=False)
    op.create_index(op.f('ix_checkins_tenant_id'), 'checkins', ['tenant_id'], unique=False)
    enable_rls('checkins')

    op.create_table('offline_snapshots',
    sa.Column('device_id', sa.Uuid(), nullable=False),
    sa.Column('snapshot_type', sa.String(), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('tenant_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_offline_snapshots_device_id'), 'offline_snapshots', ['device_id'], unique=False)
    op.create_index(op.f('ix_offline_snapshots_tenant_id'), 'offline_snapshots', ['tenant_id'], unique=False)
    enable_rls('offline_snapshots')


def downgrade() -> None:
    disable_rls('offline_snapshots')
    op.drop_index(op.f('ix_offline_snapshots_tenant_id'), table_name='offline_snapshots')
    op.drop_index(op.f('ix_offline_snapshots_device_id'), table_name='offline_snapshots')
    op.drop_table('offline_snapshots')
    
    disable_rls('checkins')
    op.drop_index(op.f('ix_checkins_tenant_id'), table_name='checkins')
    op.drop_index(op.f('ix_checkins_member_id'), table_name='checkins')
    op.drop_index(op.f('ix_checkins_location_id'), table_name='checkins')
    op.drop_index(op.f('ix_checkins_device_id'), table_name='checkins')
    op.drop_table('checkins')
    
    disable_rls('access_attempts')
    op.drop_index(op.f('ix_access_attempts_tenant_id'), table_name='access_attempts')
    op.drop_index(op.f('ix_access_attempts_member_id'), table_name='access_attempts')
    op.drop_index(op.f('ix_access_attempts_device_id'), table_name='access_attempts')
    op.drop_table('access_attempts')
    
    disable_rls('devices')
    op.drop_index(op.f('ix_devices_tenant_id'), table_name='devices')
    op.drop_index(op.f('ix_devices_location_id'), table_name='devices')
    op.drop_table('devices')
    
    disable_rls('signing_keys')
    op.drop_index(op.f('ix_signing_keys_tenant_id'), table_name='signing_keys')
    op.drop_index(op.f('ix_signing_keys_kid'), table_name='signing_keys')
    op.drop_table('signing_keys')

    sa.Enum(name='access_status_enum').drop(op.get_bind())
    sa.Enum(name='device_status_enum').drop(op.get_bind())
    sa.Enum(name='key_status_enum').drop(op.get_bind())
