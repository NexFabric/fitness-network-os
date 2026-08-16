"""Domain models for Group Class & Personal Training (PT) Booking Engine.

Adheres to GymClubNex Tenancy (TenantMixin), Composite Foreign Keys,
and PostgreSQL RLS Isolation policies.
"""

from __future__ import annotations

import enum
from datetime import datetime, time
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    Time,
    Uuid,
    column,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin

# ---------------------------------------------------------
# Enums
# ---------------------------------------------------------


class ClassSessionStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ClassBookingStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    WAITLISTED = "WAITLISTED"
    ATTENDED = "ATTENDED"
    NO_SHOW = "NO_SHOW"
    CANCELLED = "CANCELLED"


class PtAppointmentStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    ATTENDED = "ATTENDED"
    NO_SHOW = "NO_SHOW"
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------
# 1. ClassType
# ---------------------------------------------------------


class ClassType(TenantMixin, Base):
    """Catalog of class definitions (e.g. Pilates, HIIT, Yoga, Spinning)."""

    __tablename__ = "class_types"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="GENERAL")
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    default_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    color_hex: Mapped[str] = mapped_column(String(7), nullable=False, default="#3B82F6")
    required_entitlement_type: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # e.g., "CLASS_PILATES" or "CLASS_GROUP"
    cancellation_cutoff_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=120
    )  # Notice required before session start to refund entitlement
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    _model_table_args = (
        Index("ix_class_types_tenant_name", "tenant_id", "name"),
        CheckConstraint("duration_minutes > 0", name="ck_class_types_duration_pos"),
        CheckConstraint("default_capacity > 0", name="ck_class_types_capacity_pos"),
        CheckConstraint(
            "cancellation_cutoff_minutes >= 0", name="ck_class_types_cutoff_nonneg"
        ),
    )


# ---------------------------------------------------------
# 2. ClassSchedule (Recurring Weekly Master Template)
# ---------------------------------------------------------


class ClassSchedule(TenantMixin, Base):
    """Recurring weekly class timetable template (e.g., Every Monday at 10:00)."""

    __tablename__ = "class_schedules"

    location_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    class_type_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    trainer_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    day_of_week: Mapped[int] = mapped_column(
        SmallInteger, nullable=False
    )  # 0 = Monday, 6 = Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "location_id"],
            ["locations.tenant_id", "locations.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "class_type_id"],
            ["class_types.tenant_id", "class_types.id"],
            ondelete="RESTRICT",
        ),
        Index(
            "ix_class_schedules_tenant_loc_day",
            "tenant_id",
            "location_id",
            "day_of_week",
        ),
        CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6", name="ck_class_schedules_dow"
        ),
        CheckConstraint("capacity > 0", name="ck_class_schedules_capacity_pos"),
        ForeignKeyConstraint(
            ["tenant_id", "trainer_user_id"],
            ["staff.tenant_id", "staff.user_id"],
            name="fk_class_schedules_trainer_staff",
            ondelete="RESTRICT",
        ),
    )


# ---------------------------------------------------------
# 3. ClassSession (Concrete Calendar Instance)
# ---------------------------------------------------------


class ClassSession(TenantMixin, Base):
    """Concrete bookable class instance occurring at a specific date and time."""

    __tablename__ = "class_sessions"

    location_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    class_type_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    schedule_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    trainer_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    start_time_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_time_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    room_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ClassSessionStatus] = mapped_column(
        SAEnum(ClassSessionStatus), nullable=False, default=ClassSessionStatus.SCHEDULED
    )

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "location_id"],
            ["locations.tenant_id", "locations.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "class_type_id"],
            ["class_types.tenant_id", "class_types.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "schedule_id"],
            ["class_schedules.tenant_id", "class_schedules.id"],
            ondelete="SET NULL",
        ),
        Index(
            "ix_class_sessions_tenant_loc_start",
            "tenant_id",
            "location_id",
            "start_time_utc",
        ),
        Index(
            "ix_class_sessions_tenant_trainer_start",
            "tenant_id",
            "trainer_user_id",
            "start_time_utc",
        ),
        CheckConstraint(
            "end_time_utc > start_time_utc", name="ck_class_sessions_time_order"
        ),
        CheckConstraint("capacity > 0", name="ck_class_sessions_capacity_pos"),
        ForeignKeyConstraint(
            ["tenant_id", "trainer_user_id"],
            ["staff.tenant_id", "staff.user_id"],
            name="fk_class_sessions_trainer_staff",
            ondelete="RESTRICT",
        ),
        Index(
            "uq_class_sessions_schedule_start",
            "tenant_id",
            "schedule_id",
            "start_time_utc",
            unique=True,
            postgresql_where=text("schedule_id IS NOT NULL"),
        ),
    )


# ---------------------------------------------------------
# 4. ClassBooking (Individual Member Reservation)
# ---------------------------------------------------------


class ClassBooking(TenantMixin, Base):
    """Booking ledger entry for a member reservation or waitlist entry."""

    __tablename__ = "class_bookings"

    session_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[ClassBookingStatus] = mapped_column(
        SAEnum(ClassBookingStatus), nullable=False, default=ClassBookingStatus.CONFIRMED
    )
    waitlist_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    booked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancellation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_late_cancellation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "session_id"],
            ["class_sessions.tenant_id", "class_sessions.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "member_id"],
            ["members.tenant_id", "members.id"],
            ondelete="CASCADE",
        ),
        # Unique active booking per member/session (CONFIRMED or WAITLISTED)
        Index(
            "uq_class_bookings_active_member",
            "tenant_id",
            "session_id",
            "member_id",
            unique=True,
            postgresql_where=text("status IN ('CONFIRMED', 'WAITLISTED')"),
        ),
        # Unique waitlist position per session
        Index(
            "uq_class_bookings_waitlist_pos",
            "tenant_id",
            "session_id",
            "waitlist_position",
            unique=True,
            postgresql_where=text(
                "status = 'WAITLISTED' AND waitlist_position IS NOT NULL"
            ),
        ),
        Index("ix_class_bookings_tenant_member", "tenant_id", "member_id"),
        Index(
            "ix_class_bookings_tenant_session_status",
            "tenant_id",
            "session_id",
            "status",
        ),
        CheckConstraint(
            "(status = 'WAITLISTED' AND waitlist_position >= 1) OR (status != 'WAITLISTED' AND waitlist_position IS NULL)",
            name="ck_class_bookings_waitlist_pos_valid",
        ),
    )


# ---------------------------------------------------------
# 5. TrainerAvailability (PT Working Hours Template)
# ---------------------------------------------------------


class TrainerAvailability(TenantMixin, Base):
    """Recurring weekly working hours and slot durations for PT trainers."""

    __tablename__ = "trainer_availabilities"

    trainer_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    day_of_week: Mapped[int] = mapped_column(
        SmallInteger, nullable=False
    )  # 0 = Monday, 6 = Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "location_id"],
            ["locations.tenant_id", "locations.id"],
            ondelete="RESTRICT",
        ),
        Index(
            "ix_trainer_avail_tenant_trainer_dow",
            "tenant_id",
            "trainer_user_id",
            "day_of_week",
        ),
        CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6", name="ck_trainer_avail_dow"
        ),
        CheckConstraint("slot_duration_minutes > 0", name="ck_trainer_avail_slot_pos"),
        ForeignKeyConstraint(
            ["tenant_id", "trainer_user_id"],
            ["staff.tenant_id", "staff.user_id"],
            name="fk_trainer_avail_trainer_staff",
            ondelete="RESTRICT",
        ),
    )


# ---------------------------------------------------------
# 6. PtAppointment (1-on-1 Personal Training Session)
# ---------------------------------------------------------


class PtAppointment(TenantMixin, Base):
    """Individual 1-on-1 Personal Training appointment booking."""

    __tablename__ = "pt_appointments"

    trainer_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    location_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    start_time_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_time_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[PtAppointmentStatus] = mapped_column(
        SAEnum(PtAppointmentStatus),
        nullable=False,
        default=PtAppointmentStatus.CONFIRMED,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    booked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "member_id"],
            ["members.tenant_id", "members.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "location_id"],
            ["locations.tenant_id", "locations.id"],
            ondelete="RESTRICT",
        ),
        Index(
            "ix_pt_appointments_tenant_trainer_time",
            "tenant_id",
            "trainer_user_id",
            "start_time_utc",
        ),
        Index(
            "ix_pt_appointments_tenant_member_time",
            "tenant_id",
            "member_id",
            "start_time_utc",
        ),
        CheckConstraint(
            "end_time_utc > start_time_utc", name="ck_pt_appointments_time_order"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "trainer_user_id"],
            ["staff.tenant_id", "staff.user_id"],
            name="fk_pt_appointments_trainer_staff",
            ondelete="RESTRICT",
        ),
        ExcludeConstraint(
            (column("tenant_id"), "="),
            (column("trainer_user_id"), "="),
            (text("tstzrange(start_time_utc, end_time_utc, '[)')"), "&&"),
            name="ex_pt_appointments_no_overlap",
            using="gist",
            where=text("status = 'CONFIRMED'"),
        ),
    )
