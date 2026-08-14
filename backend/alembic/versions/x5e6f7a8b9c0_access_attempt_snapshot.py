"""add snapshot_data to access_attempts

Revision ID: x5e6f7a8b9c0
Revises: x4d5e6f7a8b9
Create Date: 2026-08-14 23:48:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "x5e6f7a8b9c0"
down_revision: Union[str, None] = "x4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "access_attempts",
        sa.Column(
            "snapshot_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Immutable forensic context snapshot at the decision moment",
        ),
    )


def downgrade() -> None:
    op.drop_column("access_attempts", "snapshot_data")
