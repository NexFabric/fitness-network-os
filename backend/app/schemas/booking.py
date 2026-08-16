"""Pydantic schemas for Group Class & PT Booking Engine."""

from __future__ import annotations

from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.booking import (
    ClassBookingStatus,
    ClassSessionStatus,
    PtAppointmentStatus,
)

# ---------------------------------------------------------
# 1. ClassType Schemas
# ---------------------------------------------------------


class ClassTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    category: str = Field("GENERAL", max_length=64)
    duration_minutes: int = Field(50, gt=0)
    default_capacity: int = Field(15, gt=0)
    color_hex: str = Field("#3B82F6", max_length=7)
    required_entitlement_type: str | None = Field(None, max_length=64)
    cancellation_cutoff_minutes: int = Field(120, ge=0)
    is_active: bool = True


class ClassTypeCreate(ClassTypeBase):
    pass


class ClassTypeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    category: str | None = Field(None, max_length=64)
    duration_minutes: int | None = Field(None, gt=0)
    default_capacity: int | None = Field(None, gt=0)
    color_hex: str | None = Field(None, max_length=7)
    required_entitlement_type: str | None = None
    cancellation_cutoff_minutes: int | None = Field(None, ge=0)
    is_active: bool | None = None


class ClassTypeResponse(ClassTypeBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# 2. ClassSchedule Schemas (Recurring Template)
# ---------------------------------------------------------


class ClassScheduleBase(BaseModel):
    location_id: UUID
    class_type_id: UUID
    trainer_user_id: UUID
    day_of_week: int = Field(..., ge=0, le=6)  # 0 = Monday, 6 = Sunday
    start_time: time
    end_time: time
    room_name: str | None = Field(None, max_length=64)
    capacity: int = Field(..., gt=0)
    is_active: bool = True


class ClassScheduleCreate(ClassScheduleBase):
    pass


class ClassScheduleUpdate(BaseModel):
    location_id: UUID | None = None
    class_type_id: UUID | None = None
    trainer_user_id: UUID | None = None
    day_of_week: int | None = Field(None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    room_name: str | None = None
    capacity: int | None = Field(None, gt=0)
    is_active: bool | None = None


class ClassScheduleResponse(ClassScheduleBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# 3. ClassSession Schemas (Concrete Calendar Instance)
# ---------------------------------------------------------


class ClassSessionBase(BaseModel):
    location_id: UUID
    class_type_id: UUID
    schedule_id: UUID | None = None
    trainer_user_id: UUID
    start_time_utc: datetime
    end_time_utc: datetime
    room_name: str | None = Field(None, max_length=64)
    capacity: int = Field(..., gt=0)
    status: ClassSessionStatus = ClassSessionStatus.SCHEDULED


class ClassSessionCreate(ClassSessionBase):
    pass


class ClassSessionUpdate(BaseModel):
    trainer_user_id: UUID | None = None
    start_time_utc: datetime | None = None
    end_time_utc: datetime | None = None
    room_name: str | None = None
    capacity: int | None = Field(None, gt=0)
    status: ClassSessionStatus | None = None


class ClassSessionResponse(ClassSessionBase):
    id: UUID
    tenant_id: UUID
    class_type_name: str | None = None
    class_type_color: str | None = None
    class_type_category: str | None = None
    trainer_name: str | None = None
    location_name: str | None = None
    confirmed_count: int = 0
    waitlist_count: int = 0
    available_spots: int = 0
    user_booking_status: ClassBookingStatus | None = None
    user_booking_id: UUID | None = None
    user_waitlist_position: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# 4. ClassBooking Schemas
# ---------------------------------------------------------


class ClassBookingCreate(BaseModel):
    session_id: UUID
    member_id: UUID | None = None  # If None, resolved to current bound member in /me


class ClassBookingCancelRequest(BaseModel):
    cancellation_reason: str | None = Field(None, max_length=255)


class ClassAttendanceUpdateRequest(BaseModel):
    status: ClassBookingStatus = Field(..., description="ATTENDED or NO_SHOW")


class ClassAttendeeResponse(BaseModel):
    booking_id: UUID
    member_id: UUID
    member_name: str
    member_email: str | None = None
    member_phone: str | None = None
    status: ClassBookingStatus
    waitlist_position: int | None = None
    booked_at: datetime
    attended_at: datetime | None = None
    cancelled_at: datetime | None = None
    is_late_cancellation: bool = False

    model_config = ConfigDict(from_attributes=True)


class ClassSessionRosterResponse(BaseModel):
    session: ClassSessionResponse
    attendees: list[ClassAttendeeResponse]
    total_confirmed: int
    total_waitlisted: int


class ClassBookingResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    session_id: UUID
    member_id: UUID
    status: ClassBookingStatus
    waitlist_position: int | None = None
    booked_at: datetime
    attended_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    is_late_cancellation: bool = False
    session: ClassSessionResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# 5. Trainer Availability Schemas
# ---------------------------------------------------------


class TrainerAvailabilityBase(BaseModel):
    trainer_user_id: UUID
    location_id: UUID
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time
    slot_duration_minutes: int = Field(60, gt=0)
    is_active: bool = True


class TrainerAvailabilityCreate(TrainerAvailabilityBase):
    pass


class TrainerAvailabilityUpdate(BaseModel):
    location_id: UUID | None = None
    day_of_week: int | None = Field(None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    slot_duration_minutes: int | None = Field(None, gt=0)
    is_active: bool | None = None


class TrainerAvailabilityResponse(TrainerAvailabilityBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# 6. Personal Training (PT) Appointment Schemas
# ---------------------------------------------------------


class PtAppointmentBase(BaseModel):
    trainer_user_id: UUID
    member_id: UUID | None = None  # If None, resolved to current bound member in /me
    location_id: UUID
    start_time_utc: datetime
    end_time_utc: datetime
    notes: str | None = None


class PtAppointmentCreate(PtAppointmentBase):
    pass


class PtAppointmentCancelRequest(BaseModel):
    cancellation_reason: str | None = Field(None, max_length=255)


class PtAppointmentAttendanceRequest(BaseModel):
    status: PtAppointmentStatus = Field(..., description="ATTENDED or NO_SHOW")


class PtAppointmentResponse(PtAppointmentBase):
    id: UUID
    tenant_id: UUID
    status: PtAppointmentStatus
    trainer_name: str | None = None
    member_name: str | None = None
    location_name: str | None = None
    booked_at: datetime
    attended_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerateSessionsRequest(BaseModel):
    schedule_id: UUID
    start_date: datetime
    end_date: datetime
