"""Endpoints for Group Classes, Schedules, Sessions, Attendance & PT."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService, SecurityException
from app.models.booking import PtAppointment
from app.models.user import User
from app.schemas.booking import (
    ClassAttendanceUpdateRequest,
    ClassBookingCancelRequest,
    ClassBookingResponse,
    ClassScheduleCreate,
    ClassScheduleResponse,
    ClassScheduleUpdate,
    ClassSessionCreate,
    ClassSessionResponse,
    ClassSessionRosterResponse,
    ClassTypeCreate,
    ClassTypeResponse,
    ClassTypeUpdate,
    GenerateSessionsRequest,
    PtAppointmentCancelRequest,
    PtAppointmentCreate,
    PtAppointmentResponse,
    TrainerAvailabilityCreate,
    TrainerAvailabilityResponse,
)
from app.services.booking import ClassBookingService, PtBookingService
from app.services.member_visibility import (
    has_tenant_wide_member_read,
    require_member_visible,
)

router = APIRouter()


def _require(user: User, tenant_id: UUID, permission: str) -> None:
    if not AuthorizationService.is_authorized(
        user=user, permission=permission, resource_tenant_id=tenant_id
    ):
        raise SecurityException()


# ---------------------------------------------------------
# Class Types (Catalog)
# ---------------------------------------------------------


@router.get("/types", response_model=list[ClassTypeResponse])
async def list_class_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
    active_only: bool = Query(True),
) -> list[ClassTypeResponse]:
    _require(current_user, tenant_id, "classes:read")
    types = await ClassBookingService.list_class_types(
        db, tenant_id=tenant_id, active_only=active_only
    )
    return [ClassTypeResponse.model_validate(t) for t in types]


@router.post(
    "/types",
    response_model=ClassTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_class_type(
    data: ClassTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ClassTypeResponse:
    _require(current_user, tenant_id, "classes:write")
    t = await ClassBookingService.create_class_type(db, tenant_id=tenant_id, data=data)
    await db.commit()
    await db.refresh(t)
    return ClassTypeResponse.model_validate(t)


@router.put(
    "/types/{class_type_id}",
    response_model=ClassTypeResponse,
)
async def update_class_type(
    class_type_id: UUID,
    data: ClassTypeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ClassTypeResponse:
    _require(current_user, tenant_id, "classes:write")
    t = await ClassBookingService.update_class_type(
        db, tenant_id=tenant_id, class_type_id=class_type_id, data=data
    )
    await db.commit()
    await db.refresh(t)
    return ClassTypeResponse.model_validate(t)


# ---------------------------------------------------------
# Class Schedules (Master Weekly Template)
# ---------------------------------------------------------


@router.get("/schedules", response_model=list[ClassScheduleResponse])
async def list_class_schedules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
    location_id: UUID | None = Query(None),
    active_only: bool = Query(True),
) -> list[ClassScheduleResponse]:
    _require(current_user, tenant_id, "classes:read")
    schedules = await ClassBookingService.list_schedules(
        db, tenant_id=tenant_id, location_id=location_id, active_only=active_only
    )
    return [ClassScheduleResponse.model_validate(s) for s in schedules]


@router.post(
    "/schedules",
    response_model=ClassScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_class_schedule(
    data: ClassScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ClassScheduleResponse:
    _require(current_user, tenant_id, "classes:write")
    s = await ClassBookingService.create_schedule(db, tenant_id=tenant_id, data=data)
    await db.commit()
    await db.refresh(s)
    return ClassScheduleResponse.model_validate(s)


@router.put(
    "/schedules/{schedule_id}",
    response_model=ClassScheduleResponse,
)
async def update_class_schedule(
    schedule_id: UUID,
    data: ClassScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ClassScheduleResponse:
    _require(current_user, tenant_id, "classes:write")
    s = await ClassBookingService.update_schedule(
        db, tenant_id=tenant_id, schedule_id=schedule_id, data=data
    )
    await db.commit()
    await db.refresh(s)
    return ClassScheduleResponse.model_validate(s)


@router.post(
    "/schedules/{schedule_id}/generate-sessions",
    response_model=list[ClassSessionResponse],
)
async def generate_sessions(
    schedule_id: UUID,
    data: GenerateSessionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
) -> list[ClassSessionResponse]:
    _require(current_user, tenant_id, "classes:write")
    await ClassBookingService.generate_sessions_from_schedule(
        db,
        tenant_id=tenant_id,
        schedule_id=schedule_id,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    await db.commit()
    return await ClassBookingService.list_sessions(
        db,
        tenant_id=tenant_id,
        start_time=data.start_date,
        end_time=data.end_date,
    )


# ---------------------------------------------------------
# Class Sessions (Calendar & Roster)
# ---------------------------------------------------------


@router.get("/sessions", response_model=list[ClassSessionResponse])
async def list_class_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
    location_id: UUID | None = Query(None),
    class_type_id: UUID | None = Query(None),
    trainer_user_id: UUID | None = Query(None),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
) -> list[ClassSessionResponse]:
    _require(current_user, tenant_id, "classes:read")
    return await ClassBookingService.list_sessions(
        db,
        tenant_id=tenant_id,
        location_id=location_id,
        class_type_id=class_type_id,
        trainer_user_id=trainer_user_id,
        start_time=start_time,
        end_time=end_time,
    )


@router.post(
    "/sessions",
    response_model=ClassSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_class_session(
    data: ClassSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ClassSessionResponse:
    _require(current_user, tenant_id, "classes:write")
    sess = await ClassBookingService.create_session(db, tenant_id=tenant_id, data=data)
    await db.commit()
    res_list = await ClassBookingService.list_sessions(
        db,
        tenant_id=tenant_id,
        start_time=sess.start_time_utc,
        end_time=sess.end_time_utc,
    )
    target = next((s for s in res_list if s.id == sess.id), None)
    if target:
        return target
    return ClassSessionResponse.model_validate(sess)


@router.get(
    "/sessions/{session_id}/roster",
    response_model=ClassSessionRosterResponse,
)
async def get_session_roster(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ClassSessionRosterResponse:
    _require(current_user, tenant_id, "classes:read")
    return await ClassBookingService.get_session_roster(
        db, tenant_id=tenant_id, session_id=session_id
    )


@router.post(
    "/bookings/{booking_id}/attend",
    response_model=ClassBookingResponse,
)
async def mark_attendance(
    booking_id: UUID,
    data: ClassAttendanceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ClassBookingResponse:
    _require(current_user, tenant_id, "classes:attend")
    booking = await ClassBookingService.mark_attendance(
        db, tenant_id=tenant_id, booking_id=booking_id, status_val=data.status
    )
    await db.commit()
    await db.refresh(booking)
    return ClassBookingResponse.model_validate(booking)


@router.post(
    "/bookings/{booking_id}/cancel",
    response_model=ClassBookingResponse,
)
async def admin_cancel_booking(
    booking_id: UUID,
    data: ClassBookingCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ClassBookingResponse:
    _require(current_user, tenant_id, "classes:write")
    booking = await ClassBookingService.cancel_booking(
        db,
        tenant_id=tenant_id,
        booking_id=booking_id,
        reason=data.cancellation_reason,
        is_staff=True,
    )
    await db.commit()
    await db.refresh(booking)
    return ClassBookingResponse.model_validate(booking)


# ---------------------------------------------------------
# Trainer Availability
# ---------------------------------------------------------


@router.get("/trainers/availability", response_model=list[TrainerAvailabilityResponse])
async def list_trainer_availabilities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
    trainer_user_id: UUID | None = Query(None),
    location_id: UUID | None = Query(None),
) -> list[TrainerAvailabilityResponse]:
    _require(current_user, tenant_id, "trainers:availability:read")
    avail = await PtBookingService.list_availabilities(
        db,
        tenant_id=tenant_id,
        trainer_user_id=trainer_user_id,
        location_id=location_id,
    )
    return [TrainerAvailabilityResponse.model_validate(a) for a in avail]


@router.post(
    "/trainers/availability",
    response_model=TrainerAvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_trainer_availability(
    data: TrainerAvailabilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TrainerAvailabilityResponse:
    _require(current_user, tenant_id, "trainers:availability:write")
    a = await PtBookingService.create_availability(db, tenant_id=tenant_id, data=data)
    await db.commit()
    await db.refresh(a)
    return TrainerAvailabilityResponse.model_validate(a)


# ---------------------------------------------------------
# Personal Training (PT) Appointments
# ---------------------------------------------------------


@router.get("/pt/appointments", response_model=list[PtAppointmentResponse])
async def list_pt_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
    trainer_user_id: UUID | None = Query(None),
    member_id: UUID | None = Query(None),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
) -> list[PtAppointmentResponse]:
    _require(current_user, tenant_id, "pt:read")
    scoped_trainer_id = trainer_user_id
    if not has_tenant_wide_member_read(current_user, tenant_id):
        scoped_trainer_id = current_user.id
    if member_id is not None:
        await require_member_visible(db, current_user, tenant_id, member_id)
    appts = await PtBookingService.list_appointments(
        db,
        tenant_id=tenant_id,
        trainer_user_id=scoped_trainer_id,
        member_id=member_id,
        start_time=start_time,
        end_time=end_time,
    )
    return [PtAppointmentResponse.model_validate(a) for a in appts]


@router.post(
    "/pt/appointments",
    response_model=PtAppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pt_appointment(
    data: PtAppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PtAppointmentResponse:
    _require(current_user, tenant_id, "pt:write")
    if not data.member_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="member_id zorunludur.",
        )
    await require_member_visible(db, current_user, tenant_id, data.member_id)
    if (
        not has_tenant_wide_member_read(current_user, tenant_id)
        and data.trainer_user_id != current_user.id
    ):
        raise SecurityException("cannot book PT as another trainer")
    appt = await PtBookingService.book_appointment(
        db,
        tenant_id=tenant_id,
        trainer_user_id=data.trainer_user_id,
        member_id=data.member_id,
        location_id=data.location_id,
        start_time_utc=data.start_time_utc,
        end_time_utc=data.end_time_utc,
        notes=data.notes,
    )
    await db.commit()
    await db.refresh(appt)
    return PtAppointmentResponse.model_validate(appt)


@router.post(
    "/pt/appointments/{appointment_id}/cancel",
    response_model=PtAppointmentResponse,
)
async def admin_cancel_pt_appointment(
    appointment_id: UUID,
    data: PtAppointmentCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PtAppointmentResponse:
    _require(current_user, tenant_id, "pt:write")
    existing = (
        await db.execute(
            select(PtAppointment).where(
                PtAppointment.tenant_id == tenant_id,
                PtAppointment.id == appointment_id,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PT randevusu bulunamadı.",
        )
    await require_member_visible(db, current_user, tenant_id, existing.member_id)
    if (
        not has_tenant_wide_member_read(current_user, tenant_id)
        and existing.trainer_user_id != current_user.id
    ):
        raise SecurityException("cannot cancel another trainer's appointment")
    appt = await PtBookingService.cancel_appointment(
        db,
        tenant_id=tenant_id,
        appointment_id=appointment_id,
        is_staff=True,
    )
    await db.commit()
    await db.refresh(appt)
    return PtAppointmentResponse.model_validate(appt)
