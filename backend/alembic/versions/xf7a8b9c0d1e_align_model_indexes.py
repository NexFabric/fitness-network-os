"""Align ORM-declared indexes with the live schema (alembic check).

Revision ID: xf7a8b9c0d1e
Revises: xe6f7a8b9c0d
Create Date: 2026-08-16 12:30:00.000000

Named federation/DSAR indexes already exist (xa1 / xe6). This revision only
creates the single-column FK/time indexes SQLAlchemy already declares on
booking tables so autogenerate stops proposing add_index.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "xf7a8b9c0d1e"
down_revision: str | Sequence[str] | None = "xe6f7a8b9c0d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_INDEXES = (
    ("ix_class_schedules_trainer_user_id", "class_schedules", ["trainer_user_id"]),
    ("ix_class_sessions_start_time_utc", "class_sessions", ["start_time_utc"]),
    ("ix_class_sessions_trainer_user_id", "class_sessions", ["trainer_user_id"]),
    ("ix_pt_appointments_start_time_utc", "pt_appointments", ["start_time_utc"]),
    ("ix_pt_appointments_trainer_user_id", "pt_appointments", ["trainer_user_id"]),
    (
        "ix_trainer_availabilities_trainer_user_id",
        "trainer_availabilities",
        ["trainer_user_id"],
    ),
)


def upgrade() -> None:
    for name, table, cols in _INDEXES:
        op.create_index(name, table, cols, if_not_exists=True)


def downgrade() -> None:
    for name, table, _cols in reversed(_INDEXES):
        op.drop_index(name, table_name=table, if_exists=True)
