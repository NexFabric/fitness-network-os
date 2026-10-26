"""Backfill staff rows and bind trainer_user_id to staff employment.

Revision ID: xh9c0d1e2f3a
Revises: xg8b9c0d1e2f
Create Date: 2026-08-16 17:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "xh9c0d1e2f3a"
down_revision: str | Sequence[str] | None = "xg8b9c0d1e2f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SOURCES = (
    "SELECT tenant_id, trainer_user_id FROM class_schedules",
    "SELECT tenant_id, trainer_user_id FROM class_sessions",
    "SELECT tenant_id, trainer_user_id FROM trainer_availabilities",
    "SELECT tenant_id, trainer_user_id FROM pt_appointments",
    "SELECT tenant_id, trainer_user_id FROM trainer_assignments",
    """
    SELECT ur.tenant_id, ur.user_id
    FROM user_roles ur
    JOIN roles r ON r.id = ur.role_id
    WHERE ur.tenant_id IS NOT NULL AND r.name = 'TRAINER'
    """,
)

_FK = (
    (
        "fk_class_schedules_trainer_staff",
        "class_schedules",
        "RESTRICT",
    ),
    (
        "fk_class_sessions_trainer_staff",
        "class_sessions",
        "RESTRICT",
    ),
    (
        "fk_trainer_avail_trainer_staff",
        "trainer_availabilities",
        "RESTRICT",
    ),
    (
        "fk_pt_appointments_trainer_staff",
        "pt_appointments",
        "RESTRICT",
    ),
    (
        "fk_trainer_assignments_trainer_staff",
        "trainer_assignments",
        "RESTRICT",
    ),
)


def upgrade() -> None:
    union = " UNION ".join(f"({src})" for src in _SOURCES)
    op.execute(
        sa.text(
            f"""
            INSERT INTO staff (id, tenant_id, user_id, role, created_at, updated_at)
            SELECT gen_random_uuid(), src.tenant_id, src.trainer_user_id, 'TRAINER',
                   NOW(), NOW()
            FROM ({union}) AS src(tenant_id, trainer_user_id)
            WHERE NOT EXISTS (
                SELECT 1 FROM staff s
                WHERE s.tenant_id = src.tenant_id
                  AND s.user_id = src.trainer_user_id
            )
            """
        )
    )
    for name, table, ondelete in _FK:
        op.create_foreign_key(
            name,
            table,
            "staff",
            ["tenant_id", "trainer_user_id"],
            ["tenant_id", "user_id"],
            ondelete=ondelete,
        )
    op.create_index(
        "uq_class_sessions_schedule_start",
        "class_sessions",
        ["tenant_id", "schedule_id", "start_time_utc"],
        unique=True,
        postgresql_where=sa.text("schedule_id IS NOT NULL"),
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_class_sessions_schedule_start",
        table_name="class_sessions",
        if_exists=True,
    )
    for name, table, _ondelete in reversed(_FK):
        op.drop_constraint(name, table, type_="foreignkey")
