"""make expected_end_date nullable

Revision ID: 6590aca081d6
Revises: q0d1e2f3a4b5
Create Date: 2026-08-11 00:18:49.074865

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6590aca081d6"
down_revision: str | Sequence[str] | None = "q0d1e2f3a4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "membership_freezes",
        "expected_end_date",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "membership_freezes",
        "expected_end_date",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
