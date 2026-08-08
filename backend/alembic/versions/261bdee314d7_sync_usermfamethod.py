"""Sync UserMfaMethod

Revision ID: 261bdee314d7
Revises: 8d7e354b271c
Create Date: 2026-08-09 01:26:35.657217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '261bdee314d7'
down_revision: Union[str, Sequence[str], None] = '8d7e354b271c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('user_mfa_methods', sa.Column('encrypted_secret', sa.String(length=255), nullable=True))
    op.add_column('user_mfa_methods', sa.Column('provider_id', sa.String(length=255), nullable=True))
    op.alter_column('user_mfa_methods', 'secret', nullable=True)
    op.alter_column('user_mfa_methods', 'method_type', nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('user_mfa_methods', 'method_type', nullable=False)
    op.alter_column('user_mfa_methods', 'secret', nullable=False)
    op.drop_column('user_mfa_methods', 'provider_id')
    op.drop_column('user_mfa_methods', 'encrypted_secret')
    # ### end Alembic commands ###
