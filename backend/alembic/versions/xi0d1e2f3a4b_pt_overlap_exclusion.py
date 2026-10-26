"""Prevent overlapping CONFIRMED PT appointments for one trainer.

Revision ID: xi0d1e2f3a4b
Revises: xh9c0d1e2f3a
Create Date: 2026-08-16 17:10:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "xi0d1e2f3a4b"
down_revision: str | Sequence[str] | None = "xh9c0d1e2f3a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        """
        ALTER TABLE pt_appointments
        ADD CONSTRAINT ex_pt_appointments_no_overlap
        EXCLUDE USING gist (
            tenant_id WITH =,
            trainer_user_id WITH =,
            tstzrange(start_time_utc, end_time_utc, '[)') WITH &&
        )
        WHERE (status = 'CONFIRMED')
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE pt_appointments DROP CONSTRAINT IF EXISTS ex_pt_appointments_no_overlap"
    )
