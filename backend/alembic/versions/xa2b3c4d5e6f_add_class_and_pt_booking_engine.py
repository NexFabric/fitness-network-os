"""Add Class and PT Booking Engine tables with RLS and seed permissions.

Revision ID: xa2b3c4d5e6f
Revises: xa1b2c3d4e5f
Create Date: 2026-08-15 21:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

from alembic import op
from app.db.rls import disable_rls, enable_rls

# revision identifiers, used by Alembic.
revision: str = "xa2b3c4d5e6f"
down_revision: str | None = "xa1b2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DO $$ BEGIN
                CREATE TYPE classsessionstatus AS ENUM ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
            """
        )
    )
    conn.execute(
        sa.text(
            """
            DO $$ BEGIN
                CREATE TYPE classbookingstatus AS ENUM ('CONFIRMED', 'WAITLISTED', 'ATTENDED', 'NO_SHOW', 'CANCELLED');
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
            """
        )
    )
    conn.execute(
        sa.text(
            """
            DO $$ BEGIN
                CREATE TYPE ptappointmentstatus AS ENUM ('CONFIRMED', 'ATTENDED', 'NO_SHOW', 'CANCELLED');
            EXCEPTION WHEN duplicate_object THEN null;
            END $$;
            """
        )
    )

    # 1. class_types
    op.create_table(
        "class_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(64), nullable=False, server_default="GENERAL"),
        sa.Column(
            "duration_minutes", sa.Integer(), nullable=False, server_default="50"
        ),
        sa.Column(
            "default_capacity", sa.Integer(), nullable=False, server_default="15"
        ),
        sa.Column("color_hex", sa.String(7), nullable=False, server_default="#3B82F6"),
        sa.Column("required_entitlement_type", sa.String(64), nullable=True),
        sa.Column(
            "cancellation_cutoff_minutes",
            sa.Integer(),
            nullable=False,
            server_default="120",
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_class_types_tenant_id"),
        sa.CheckConstraint("duration_minutes > 0", name="ck_class_types_duration_pos"),
        sa.CheckConstraint("default_capacity > 0", name="ck_class_types_capacity_pos"),
        sa.CheckConstraint(
            "cancellation_cutoff_minutes >= 0", name="ck_class_types_cutoff_nonneg"
        ),
    )
    op.create_index("ix_class_types_tenant_id", "class_types", ["tenant_id"])
    op.create_index("ix_class_types_tenant_name", "class_types", ["tenant_id", "name"])
    enable_rls("class_types")

    # 2. class_schedules
    op.create_table(
        "class_schedules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("class_type_id", sa.Uuid(), nullable=False),
        sa.Column("trainer_user_id", sa.Uuid(), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("room_name", sa.String(64), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_class_schedules_tenant_id"),
        sa.ForeignKeyConstraint(
            ["trainer_user_id"],
            ["users.id"],
            name="fk_class_schedules_trainer_user_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "location_id"],
            ["locations.tenant_id", "locations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "class_type_id"],
            ["class_types.tenant_id", "class_types.id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6", name="ck_class_schedules_dow"
        ),
        sa.CheckConstraint("capacity > 0", name="ck_class_schedules_capacity_pos"),
    )
    op.create_index("ix_class_schedules_tenant_id", "class_schedules", ["tenant_id"])
    op.create_index(
        "ix_class_schedules_tenant_loc_day",
        "class_schedules",
        ["tenant_id", "location_id", "day_of_week"],
    )
    enable_rls("class_schedules")

    # 3. class_sessions
    op.create_table(
        "class_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("class_type_id", sa.Uuid(), nullable=False),
        sa.Column("schedule_id", sa.Uuid(), nullable=True),
        sa.Column("trainer_user_id", sa.Uuid(), nullable=False),
        sa.Column("start_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("room_name", sa.String(64), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            PG_ENUM(
                "SCHEDULED",
                "IN_PROGRESS",
                "COMPLETED",
                "CANCELLED",
                name="classsessionstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="SCHEDULED",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_class_sessions_tenant_id"),
        sa.ForeignKeyConstraint(
            ["trainer_user_id"],
            ["users.id"],
            name="fk_class_sessions_trainer_user_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "location_id"],
            ["locations.tenant_id", "locations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "class_type_id"],
            ["class_types.tenant_id", "class_types.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "schedule_id"],
            ["class_schedules.tenant_id", "class_schedules.id"],
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "end_time_utc > start_time_utc", name="ck_class_sessions_time_order"
        ),
        sa.CheckConstraint("capacity > 0", name="ck_class_sessions_capacity_pos"),
    )
    op.create_index("ix_class_sessions_tenant_id", "class_sessions", ["tenant_id"])
    op.create_index(
        "ix_class_sessions_tenant_loc_start",
        "class_sessions",
        ["tenant_id", "location_id", "start_time_utc"],
    )
    op.create_index(
        "ix_class_sessions_tenant_trainer_start",
        "class_sessions",
        ["tenant_id", "trainer_user_id", "start_time_utc"],
    )
    enable_rls("class_sessions")

    # 4. class_bookings
    op.create_table(
        "class_bookings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            PG_ENUM(
                "CONFIRMED",
                "WAITLISTED",
                "ATTENDED",
                "NO_SHOW",
                "CANCELLED",
                name="classbookingstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="CONFIRMED",
        ),
        sa.Column("waitlist_position", sa.Integer(), nullable=True),
        sa.Column("booked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.String(255), nullable=True),
        sa.Column(
            "is_late_cancellation",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_class_bookings_tenant_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "session_id"],
            ["class_sessions.tenant_id", "class_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "member_id"],
            ["members.tenant_id", "members.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "(status = 'WAITLISTED' AND waitlist_position >= 1) OR (status != 'WAITLISTED' AND waitlist_position IS NULL)",
            name="ck_class_bookings_waitlist_pos_valid",
        ),
    )
    op.create_index("ix_class_bookings_tenant_id", "class_bookings", ["tenant_id"])
    op.create_index(
        "ix_class_bookings_tenant_member", "class_bookings", ["tenant_id", "member_id"]
    )
    op.create_index(
        "ix_class_bookings_tenant_session_status",
        "class_bookings",
        ["tenant_id", "session_id", "status"],
    )
    op.create_index(
        "uq_class_bookings_active_member",
        "class_bookings",
        ["tenant_id", "session_id", "member_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('CONFIRMED', 'WAITLISTED')"),
    )
    op.create_index(
        "uq_class_bookings_waitlist_pos",
        "class_bookings",
        ["tenant_id", "session_id", "waitlist_position"],
        unique=True,
        postgresql_where=sa.text(
            "status = 'WAITLISTED' AND waitlist_position IS NOT NULL"
        ),
    )
    enable_rls("class_bookings")

    # 5. trainer_availabilities
    op.create_table(
        "trainer_availabilities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("trainer_user_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column(
            "slot_duration_minutes", sa.Integer(), nullable=False, server_default="60"
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "id", name="uq_trainer_availabilities_tenant_id"
        ),
        sa.ForeignKeyConstraint(
            ["trainer_user_id"],
            ["users.id"],
            name="fk_trainer_availabilities_trainer_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "location_id"],
            ["locations.tenant_id", "locations.id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6", name="ck_trainer_avail_dow"
        ),
        sa.CheckConstraint(
            "slot_duration_minutes > 0", name="ck_trainer_avail_slot_pos"
        ),
    )
    op.create_index(
        "ix_trainer_availabilities_tenant_id", "trainer_availabilities", ["tenant_id"]
    )
    op.create_index(
        "ix_trainer_avail_tenant_trainer_dow",
        "trainer_availabilities",
        ["tenant_id", "trainer_user_id", "day_of_week"],
    )
    enable_rls("trainer_availabilities")

    # 6. pt_appointments
    op.create_table(
        "pt_appointments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("trainer_user_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=False),
        sa.Column("start_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            PG_ENUM(
                "CONFIRMED",
                "ATTENDED",
                "NO_SHOW",
                "CANCELLED",
                name="ptappointmentstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="CONFIRMED",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("booked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_pt_appointments_tenant_id"),
        sa.ForeignKeyConstraint(
            ["trainer_user_id"],
            ["users.id"],
            name="fk_pt_appointments_trainer_user_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "member_id"],
            ["members.tenant_id", "members.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "location_id"],
            ["locations.tenant_id", "locations.id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "end_time_utc > start_time_utc", name="ck_pt_appointments_time_order"
        ),
    )
    op.create_index("ix_pt_appointments_tenant_id", "pt_appointments", ["tenant_id"])
    op.create_index(
        "ix_pt_appointments_tenant_trainer_time",
        "pt_appointments",
        ["tenant_id", "trainer_user_id", "start_time_utc"],
    )
    op.create_index(
        "ix_pt_appointments_tenant_member_time",
        "pt_appointments",
        ["tenant_id", "member_id", "start_time_utc"],
    )
    enable_rls("pt_appointments")

    # 7. Seed Permissions
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO permissions (id, name, description, created_at, updated_at)
            VALUES 
                (gen_random_uuid(), 'classes:read', 'Read class types, schedules, and session rosters', now(), now()),
                (gen_random_uuid(), 'classes:write', 'Create and manage class types, schedules, and sessions', now(), now()),
                (gen_random_uuid(), 'classes:attend', 'Mark attendance and no-shows for group class sessions', now(), now()),
                (gen_random_uuid(), 'classes:read:self', 'Read available class schedule and own bookings via /me', now(), now()),
                (gen_random_uuid(), 'classes:book:self', 'Book, waitlist, and cancel own class sessions via /me', now(), now()),
                (gen_random_uuid(), 'pt:read', 'Read PT appointments and trainer availability', now(), now()),
                (gen_random_uuid(), 'pt:write', 'Create and manage PT appointments', now(), now()),
                (gen_random_uuid(), 'pt:read:self', 'Read own PT appointments via /me', now(), now()),
                (gen_random_uuid(), 'pt:book:self', 'Book and cancel own PT appointments via /me', now(), now()),
                (gen_random_uuid(), 'trainers:availability:read', 'Read trainer working hours and availability', now(), now()),
                (gen_random_uuid(), 'trainers:availability:write', 'Manage trainer working hours and availability', now(), now())
            ON CONFLICT (name) DO NOTHING;
            """
        )
    )

    # 8. Grant to roles
    # GYM_OWNER, GYM_ADMIN, GYM_MANAGER: classes:read, classes:write, classes:attend, pt:read, pt:write, trainers:availability:read, trainers:availability:write
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            CROSS JOIN permissions p
            WHERE r.name IN ('GYM_OWNER', 'GYM_ADMIN', 'GYM_MANAGER')
              AND p.name IN (
                  'classes:read', 'classes:write', 'classes:attend',
                  'pt:read', 'pt:write',
                  'trainers:availability:read', 'trainers:availability:write'
              )
            ON CONFLICT DO NOTHING;
            """
        )
    )

    # FRONT_DESK: classes:read, classes:attend, pt:read, trainers:availability:read
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            CROSS JOIN permissions p
            WHERE r.name = 'FRONT_DESK'
              AND p.name IN ('classes:read', 'classes:attend', 'pt:read', 'trainers:availability:read')
            ON CONFLICT DO NOTHING;
            """
        )
    )

    # TRAINER: classes:read, classes:attend, pt:read, pt:write, trainers:availability:read, trainers:availability:write
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            CROSS JOIN permissions p
            WHERE r.name = 'TRAINER'
              AND p.name IN (
                  'classes:read', 'classes:attend',
                  'pt:read', 'pt:write',
                  'trainers:availability:read', 'trainers:availability:write'
              )
            ON CONFLICT DO NOTHING;
            """
        )
    )

    # MEMBER: classes:read:self, classes:book:self, pt:read:self, pt:book:self
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            CROSS JOIN permissions p
            WHERE r.name = 'MEMBER'
              AND p.name IN ('classes:read:self', 'classes:book:self', 'pt:read:self', 'pt:book:self')
            ON CONFLICT DO NOTHING;
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE permission_id IN (
                SELECT id FROM permissions
                WHERE name IN (
                    'classes:read', 'classes:write', 'classes:attend',
                    'classes:read:self', 'classes:book:self',
                    'pt:read', 'pt:write', 'pt:read:self', 'pt:book:self',
                    'trainers:availability:read', 'trainers:availability:write'
                )
            );
            """
        )
    )
    conn.execute(
        sa.text(
            """
            DELETE FROM permissions
            WHERE name IN (
                'classes:read', 'classes:write', 'classes:attend',
                'classes:read:self', 'classes:book:self',
                'pt:read', 'pt:write', 'pt:read:self', 'pt:book:self',
                'trainers:availability:read', 'trainers:availability:write'
            );
            """
        )
    )

    disable_rls("pt_appointments")
    op.drop_table("pt_appointments")
    conn.execute(sa.text("DROP TYPE IF EXISTS ptappointmentstatus CASCADE;"))

    disable_rls("trainer_availabilities")
    op.drop_table("trainer_availabilities")

    disable_rls("class_bookings")
    op.drop_table("class_bookings")
    conn.execute(sa.text("DROP TYPE IF EXISTS classbookingstatus CASCADE;"))

    disable_rls("class_sessions")
    op.drop_table("class_sessions")
    conn.execute(sa.text("DROP TYPE IF EXISTS classsessionstatus CASCADE;"))

    disable_rls("class_schedules")
    op.drop_table("class_schedules")

    disable_rls("class_types")
    op.drop_table("class_types")
