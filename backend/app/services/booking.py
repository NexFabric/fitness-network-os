"""Service layer for Group Class & Personal Training (PT) Booking Engine.

Implements pessimistic write locks (SELECT ... FOR UPDATE),
monotonic waitlist queue ordering and automatic promotion,
entitlement wallet validation, and transactional outbox events.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class BookingError(Exception):
    """HTTP-facing booking failure. Mapped at the API edge / FastAPI handler."""

    status_code = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class BookingNotFound(BookingError):
    status_code = 404


class BookingConflict(BookingError):
    status_code = 409


class BookingForbidden(BookingError):
    status_code = 403


class BookingInvalid(BookingError):
    status_code = 400


from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_types import (
    CLASS_BOOKING_CANCELLED_V1,
    CLASS_BOOKING_CONFIRMED_V1,
    CLASS_BOOKING_PROMOTED_V1,
    CLASS_BOOKING_WAITLISTED_V1,
    PT_APPOINTMENT_CANCELLED_V1,
    PT_APPOINTMENT_CONFIRMED_V1,
)
from app.models.booking import (
    ClassBooking,
    ClassBookingStatus,
    ClassSchedule,
    ClassSession,
    ClassSessionStatus,
    ClassType,
    PtAppointment,
    PtAppointmentStatus,
    TrainerAvailability,
)
from app.models.location import Location
from app.models.member import Member
from app.models.user import User
from app.schemas.booking import (
    ClassAttendeeResponse,
    ClassScheduleCreate,
    ClassScheduleUpdate,
    ClassSessionCreate,
    ClassSessionResponse,
    ClassSessionRosterResponse,
    ClassTypeCreate,
    ClassTypeUpdate,
    TrainerAvailabilityCreate,
)
from app.services.entitlement import EntitlementService
from app.services.outbox import OutboxService
from app.services.staff import CLASS_TRAINER_ROLES, PT_TRAINER_ROLES, StaffService


class ClassBookingService:
    """Core domain logic for Class Catalog, Recurring Schedules, Concrete Sessions & Bookings."""

    # ---------------------------------------------------------
    # Class Types (Catalog)
    # ---------------------------------------------------------

    @staticmethod
    async def create_class_type(
        db: AsyncSession, tenant_id: UUID, data: ClassTypeCreate
    ) -> ClassType:
        class_type = ClassType(
            id=uuid4(),
            tenant_id=tenant_id,
            name=data.name,
            category=data.category,
            duration_minutes=data.duration_minutes,
            default_capacity=data.default_capacity,
            color_hex=data.color_hex,
            required_entitlement_type=data.required_entitlement_type,
            cancellation_cutoff_minutes=data.cancellation_cutoff_minutes,
            is_active=data.is_active,
        )
        db.add(class_type)
        await db.flush()
        return class_type

    @staticmethod
    async def list_class_types(
        db: AsyncSession, tenant_id: UUID, active_only: bool = True
    ) -> list[ClassType]:
        stmt = select(ClassType).where(ClassType.tenant_id == tenant_id)
        if active_only:
            stmt = stmt.where(ClassType.is_active.is_(True))
        stmt = stmt.order_by(ClassType.name.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_class_type(
        db: AsyncSession, tenant_id: UUID, class_type_id: UUID
    ) -> ClassType:
        stmt = select(ClassType).where(
            ClassType.tenant_id == tenant_id, ClassType.id == class_type_id
        )
        result = await db.execute(stmt)
        class_type = result.scalar_one_or_none()
        if not class_type:
            raise BookingNotFound("Ders tipi bulunamadı.")
        return class_type

    @staticmethod
    async def update_class_type(
        db: AsyncSession,
        tenant_id: UUID,
        class_type_id: UUID,
        data: ClassTypeUpdate,
    ) -> ClassType:
        class_type = await ClassBookingService.get_class_type(
            db, tenant_id, class_type_id
        )
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(class_type, key, value)
        await db.flush()
        return class_type

    # ---------------------------------------------------------
    # Class Schedules (Master Weekly Recurrence)
    # ---------------------------------------------------------

    @staticmethod
    async def _require_class_trainer(
        db: AsyncSession, tenant_id: UUID, trainer_user_id: UUID
    ) -> None:
        if not await StaffService.has_tenant_role(
            db, tenant_id, trainer_user_id, CLASS_TRAINER_ROLES
        ):
            raise BookingInvalid("Eğitmen bu kulüpte tanımlı değil.")
        if not await StaffService.is_employed(db, tenant_id, trainer_user_id):
            raise BookingInvalid("Eğitmen bu kulüpte personel olarak tanımlı değil.")

    @staticmethod
    async def create_schedule(
        db: AsyncSession, tenant_id: UUID, data: ClassScheduleCreate
    ) -> ClassSchedule:
        # Verify foreign keys
        await ClassBookingService.get_class_type(db, tenant_id, data.class_type_id)
        await ClassBookingService._require_class_trainer(
            db, tenant_id, data.trainer_user_id
        )

        schedule = ClassSchedule(
            id=uuid4(),
            tenant_id=tenant_id,
            location_id=data.location_id,
            class_type_id=data.class_type_id,
            trainer_user_id=data.trainer_user_id,
            day_of_week=data.day_of_week,
            start_time=data.start_time,
            end_time=data.end_time,
            room_name=data.room_name,
            capacity=data.capacity,
            is_active=data.is_active,
        )
        db.add(schedule)
        await db.flush()
        return schedule

    @staticmethod
    async def list_schedules(
        db: AsyncSession,
        tenant_id: UUID,
        location_id: UUID | None = None,
        active_only: bool = True,
    ) -> list[ClassSchedule]:
        stmt = select(ClassSchedule).where(ClassSchedule.tenant_id == tenant_id)
        if location_id:
            stmt = stmt.where(ClassSchedule.location_id == location_id)
        if active_only:
            stmt = stmt.where(ClassSchedule.is_active.is_(True))
        stmt = stmt.order_by(
            ClassSchedule.day_of_week.asc(), ClassSchedule.start_time.asc()
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_schedule(
        db: AsyncSession,
        tenant_id: UUID,
        schedule_id: UUID,
        data: ClassScheduleUpdate,
    ) -> ClassSchedule:
        stmt = select(ClassSchedule).where(
            ClassSchedule.tenant_id == tenant_id, ClassSchedule.id == schedule_id
        )
        result = await db.execute(stmt)
        schedule = result.scalar_one_or_none()
        if not schedule:
            raise BookingNotFound("Ders programı şablonu bulunamadı.")
        updates = data.model_dump(exclude_unset=True)
        if "trainer_user_id" in updates and updates["trainer_user_id"] is not None:
            await ClassBookingService._require_class_trainer(
                db, tenant_id, updates["trainer_user_id"]
            )
        for key, value in updates.items():
            setattr(schedule, key, value)
        await db.flush()
        return schedule

    @staticmethod
    async def generate_sessions_from_schedule(
        db: AsyncSession,
        tenant_id: UUID,
        schedule_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[ClassSession]:
        stmt = select(ClassSchedule).where(
            ClassSchedule.tenant_id == tenant_id, ClassSchedule.id == schedule_id
        )
        result = await db.execute(stmt)
        schedule = result.scalar_one_or_none()
        if not schedule or not schedule.is_active:
            raise BookingNotFound("Aktif ders programı şablonu bulunamadı.")

        loc = (
            await db.execute(
                select(Location).where(
                    Location.tenant_id == tenant_id,
                    Location.id == schedule.location_id,
                )
            )
        ).scalar_one_or_none()
        if loc is None:
            raise BookingNotFound("Şube bulunamadı.")
        try:
            loc_tz = ZoneInfo(loc.timezone or "UTC")
        except ZoneInfoNotFoundError as exc:
            raise BookingInvalid("Şube saat dilimi geçersiz.") from exc

        created_sessions: list[ClassSession] = []
        curr = start_date.date()
        end_d = end_date.date()

        while curr <= end_d:
            # Python weekday: 0 = Monday, 6 = Sunday
            if curr.weekday() == schedule.day_of_week:
                session_start = datetime.combine(
                    curr, schedule.start_time, tzinfo=loc_tz
                ).astimezone(UTC)
                session_end = datetime.combine(
                    curr, schedule.end_time, tzinfo=loc_tz
                ).astimezone(UTC)
                if session_end <= session_start:
                    session_end = session_end + timedelta(days=1)

                # Check if session already exists for this schedule & start time
                dup_stmt = select(ClassSession).where(
                    ClassSession.tenant_id == tenant_id,
                    ClassSession.schedule_id == schedule.id,
                    ClassSession.start_time_utc == session_start,
                )
                dup_res = await db.execute(dup_stmt)
                if not dup_res.scalar_one_or_none():
                    session = ClassSession(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        location_id=schedule.location_id,
                        class_type_id=schedule.class_type_id,
                        schedule_id=schedule.id,
                        trainer_user_id=schedule.trainer_user_id,
                        start_time_utc=session_start,
                        end_time_utc=session_end,
                        room_name=schedule.room_name,
                        capacity=schedule.capacity,
                        status=ClassSessionStatus.SCHEDULED,
                    )
                    db.add(session)
                    created_sessions.append(session)

            curr += timedelta(days=1)

        await db.flush()
        return created_sessions

    # ---------------------------------------------------------
    # Class Sessions (Concrete Calendar Instances)
    # ---------------------------------------------------------

    @staticmethod
    async def create_session(
        db: AsyncSession, tenant_id: UUID, data: ClassSessionCreate
    ) -> ClassSession:
        await ClassBookingService.get_class_type(db, tenant_id, data.class_type_id)
        await ClassBookingService._require_class_trainer(
            db, tenant_id, data.trainer_user_id
        )

        session = ClassSession(
            id=uuid4(),
            tenant_id=tenant_id,
            location_id=data.location_id,
            class_type_id=data.class_type_id,
            schedule_id=data.schedule_id,
            trainer_user_id=data.trainer_user_id,
            start_time_utc=data.start_time_utc,
            end_time_utc=data.end_time_utc,
            room_name=data.room_name,
            capacity=data.capacity,
            status=data.status,
        )
        db.add(session)
        await db.flush()
        return session

    @staticmethod
    async def list_sessions(
        db: AsyncSession,
        tenant_id: UUID,
        location_id: UUID | None = None,
        class_type_id: UUID | None = None,
        trainer_user_id: UUID | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        member_id: UUID | None = None,
        session_id: UUID | None = None,
        schedule_id: UUID | None = None,
    ) -> list[ClassSessionResponse]:
        """Fetch sessions with enriched capacity counts and optional member-specific booking status."""
        stmt = (
            select(
                ClassSession,
                ClassType.name.label("class_type_name"),
                ClassType.color_hex.label("class_type_color"),
                ClassType.category.label("class_type_category"),
                User.email.label("trainer_name"),
                Location.name.label("location_name"),
            )
            .join(ClassType, ClassType.id == ClassSession.class_type_id)
            .join(User, User.id == ClassSession.trainer_user_id)
            .join(Location, Location.id == ClassSession.location_id)
            .where(ClassSession.tenant_id == tenant_id)
        )

        if location_id:
            stmt = stmt.where(ClassSession.location_id == location_id)
        if class_type_id:
            stmt = stmt.where(ClassSession.class_type_id == class_type_id)
        if trainer_user_id:
            stmt = stmt.where(ClassSession.trainer_user_id == trainer_user_id)
        if start_time:
            stmt = stmt.where(ClassSession.start_time_utc >= start_time)
        if end_time:
            stmt = stmt.where(ClassSession.start_time_utc <= end_time)
        if session_id:
            stmt = stmt.where(ClassSession.id == session_id)
        if schedule_id:
            stmt = stmt.where(ClassSession.schedule_id == schedule_id)

        stmt = stmt.order_by(ClassSession.start_time_utc.asc())
        result = await db.execute(stmt)
        rows = result.all()

        if not rows:
            return []

        session_ids = [r[0].id for r in rows]

        # Aggregate confirmed & waitlist counts per session
        count_stmt = (
            select(
                ClassBooking.session_id,
                ClassBooking.status,
                func.count(ClassBooking.id).label("count"),
            )
            .where(
                ClassBooking.tenant_id == tenant_id,
                ClassBooking.session_id.in_(session_ids),
                ClassBooking.status.in_(
                    [ClassBookingStatus.CONFIRMED, ClassBookingStatus.WAITLISTED]
                ),
            )
            .group_by(ClassBooking.session_id, ClassBooking.status)
        )
        count_res = await db.execute(count_stmt)
        count_map: dict[UUID, dict[str, int]] = {}
        for sess_id, st, cnt in count_res.all():
            count_map.setdefault(sess_id, {})[
                st.value if hasattr(st, "value") else str(st)
            ] = cnt

        # If member_id given, check active bookings for this member
        member_bookings: dict[UUID, ClassBooking] = {}
        if member_id:
            mb_stmt = select(ClassBooking).where(
                ClassBooking.tenant_id == tenant_id,
                ClassBooking.member_id == member_id,
                ClassBooking.session_id.in_(session_ids),
                ClassBooking.status.in_(
                    [ClassBookingStatus.CONFIRMED, ClassBookingStatus.WAITLISTED]
                ),
            )
            mb_res = await db.execute(mb_stmt)
            for mb in mb_res.scalars().all():
                member_bookings[mb.session_id] = mb

        out: list[ClassSessionResponse] = []
        for sess, ct_name, ct_color, ct_cat, tr_name, loc_name in rows:
            counts = count_map.get(sess.id, {})
            conf_cnt = counts.get(ClassBookingStatus.CONFIRMED.value, 0)
            wait_cnt = counts.get(ClassBookingStatus.WAITLISTED.value, 0)
            avail = max(0, sess.capacity - conf_cnt)

            user_b = member_bookings.get(sess.id)

            out.append(
                ClassSessionResponse(
                    id=sess.id,
                    tenant_id=sess.tenant_id,
                    location_id=sess.location_id,
                    class_type_id=sess.class_type_id,
                    schedule_id=sess.schedule_id,
                    trainer_user_id=sess.trainer_user_id,
                    start_time_utc=sess.start_time_utc,
                    end_time_utc=sess.end_time_utc,
                    room_name=sess.room_name,
                    capacity=sess.capacity,
                    status=sess.status,
                    class_type_name=ct_name,
                    class_type_color=ct_color,
                    class_type_category=ct_cat,
                    trainer_name=tr_name,
                    location_name=loc_name,
                    confirmed_count=conf_cnt,
                    waitlist_count=wait_cnt,
                    available_spots=avail,
                    user_booking_status=user_b.status if user_b else None,
                    user_booking_id=user_b.id if user_b else None,
                    user_waitlist_position=user_b.waitlist_position if user_b else None,
                    created_at=sess.created_at,
                    updated_at=sess.updated_at,
                )
            )

        return out

    @staticmethod
    async def get_session_roster(
        db: AsyncSession, tenant_id: UUID, session_id: UUID
    ) -> ClassSessionRosterResponse:
        """Fetch concrete session details and full list of confirmed + waitlisted attendees."""
        # 1. Fetch Session
        session_list = await ClassBookingService.list_sessions(
            db, tenant_id=tenant_id, session_id=session_id
        )
        target_session = next((s for s in session_list if s.id == session_id), None)
        if not target_session:
            raise BookingNotFound("Ders seansı bulunamadı.")

        # 2. Fetch Attendees
        stmt = (
            select(ClassBooking, Member)
            .join(Member, Member.id == ClassBooking.member_id)
            .where(
                ClassBooking.tenant_id == tenant_id,
                ClassBooking.session_id == session_id,
                ClassBooking.status.in_(
                    [
                        ClassBookingStatus.CONFIRMED,
                        ClassBookingStatus.WAITLISTED,
                        ClassBookingStatus.ATTENDED,
                        ClassBookingStatus.NO_SHOW,
                    ]
                ),
            )
            .order_by(
                ClassBooking.status.asc(),
                ClassBooking.waitlist_position.asc().nulls_first(),
                ClassBooking.booked_at.asc(),
            )
        )
        res = await db.execute(stmt)

        attendees: list[ClassAttendeeResponse] = []
        for b, m in res.all():
            attendees.append(
                ClassAttendeeResponse(
                    booking_id=b.id,
                    member_id=m.id,
                    member_name=f"{m.first_name} {m.last_name}",
                    member_email=m.email,
                    member_phone=m.phone,
                    status=b.status,
                    waitlist_position=b.waitlist_position,
                    booked_at=b.booked_at,
                    attended_at=b.attended_at,
                    cancelled_at=b.cancelled_at,
                    is_late_cancellation=b.is_late_cancellation,
                )
            )

        total_conf = sum(
            1
            for a in attendees
            if a.status
            in [
                ClassBookingStatus.CONFIRMED,
                ClassBookingStatus.ATTENDED,
                ClassBookingStatus.NO_SHOW,
            ]
        )
        total_wait = sum(
            1 for a in attendees if a.status == ClassBookingStatus.WAITLISTED
        )

        return ClassSessionRosterResponse(
            session=target_session,
            attendees=attendees,
            total_confirmed=total_conf,
            total_waitlisted=total_wait,
        )

    # ---------------------------------------------------------
    # Booking Engine & Concurrency Locks (Pessimistic Lock & Waitlist)
    # ---------------------------------------------------------

    @staticmethod
    async def book_session(
        db: AsyncSession,
        tenant_id: UUID,
        session_id: UUID,
        member_id: UUID,
    ) -> ClassBooking:
        """Reserve a spot in a class session with SELECT ... FOR UPDATE pessimistic lock.

        If capacity is available, creates CONFIRMED booking.
        If capacity is full, creates WAITLISTED booking with monotonic position.
        Emits outbox event.
        """
        now = datetime.now(UTC)

        # 1. Pessimistic lock on ClassSession row
        sess_stmt = (
            select(ClassSession)
            .where(ClassSession.tenant_id == tenant_id, ClassSession.id == session_id)
            .with_for_update()
        )
        sess_res = await db.execute(sess_stmt)
        session = sess_res.scalar_one_or_none()

        if not session:
            raise BookingNotFound("Ders seansı bulunamadı.")

        if session.status != ClassSessionStatus.SCHEDULED:
            raise BookingInvalid("Bu ders seansı rezervasyona kapalıdır.")

        if session.start_time_utc <= now:
            raise BookingInvalid("Geçmiş seanslara rezervasyon yapılamaz.")

        class_type = await ClassBookingService.get_class_type(
            db, tenant_id, session.class_type_id
        )
        if class_type.required_entitlement_type:
            access = await EntitlementService.check_access(
                db,
                tenant_id,
                member_id,
                class_type.required_entitlement_type,
            )
            if not access.get("granted"):
                raise BookingForbidden(
                    "Bu ders için geçerli hakkınız bulunmuyor."
                )

        # 2. Check if member already has active reservation (CONFIRMED or WAITLISTED)
        existing_stmt = select(ClassBooking).where(
            ClassBooking.tenant_id == tenant_id,
            ClassBooking.session_id == session_id,
            ClassBooking.member_id == member_id,
            ClassBooking.status.in_(
                [ClassBookingStatus.CONFIRMED, ClassBookingStatus.WAITLISTED]
            ),
        )
        existing_res = await db.execute(existing_stmt)
        if existing_res.scalar_one_or_none():
            raise BookingInvalid("Zaten bu derse aktif rezervasyonunuz bulunmaktadır.")

        # 3. Count current CONFIRMED bookings under the lock
        count_stmt = select(func.count(ClassBooking.id)).where(
            ClassBooking.tenant_id == tenant_id,
            ClassBooking.session_id == session_id,
            ClassBooking.status == ClassBookingStatus.CONFIRMED,
        )
        count_res = await db.execute(count_stmt)
        confirmed_count = count_res.scalar_one()

        outbox = OutboxService(db)

        # 4. Check available capacity
        if confirmed_count < session.capacity:
            # Capacity available -> CONFIRMED
            booking = ClassBooking(
                id=uuid4(),
                tenant_id=tenant_id,
                session_id=session_id,
                member_id=member_id,
                status=ClassBookingStatus.CONFIRMED,
                waitlist_position=None,
                booked_at=now,
            )
            db.add(booking)
            await db.flush()

            # Emit outbox event
            await outbox.enqueue(
                tenant_id=tenant_id,
                event_type=CLASS_BOOKING_CONFIRMED_V1,
                payload={
                    "booking_id": str(booking.id),
                    "session_id": str(session.id),
                    "member_id": str(member_id),
                    "start_time_utc": session.start_time_utc.isoformat(),
                },
                aggregate_type="class_booking",
                aggregate_id=booking.id,
            )
            return booking

        else:
            # Capacity full -> WAITLISTED
            max_pos_stmt = select(
                func.coalesce(func.max(ClassBooking.waitlist_position), 0)
            ).where(
                ClassBooking.tenant_id == tenant_id,
                ClassBooking.session_id == session_id,
                ClassBooking.status == ClassBookingStatus.WAITLISTED,
            )
            max_pos_res = await db.execute(max_pos_stmt)
            current_max = max_pos_res.scalar_one_or_none()
            next_pos = (int(current_max) if current_max is not None else 0) + 1

            booking = ClassBooking(
                id=uuid4(),
                tenant_id=tenant_id,
                session_id=session_id,
                member_id=member_id,
                status=ClassBookingStatus.WAITLISTED,
                waitlist_position=next_pos,
                booked_at=now,
            )
            db.add(booking)
            await db.flush()

            # Emit outbox event
            await outbox.enqueue(
                tenant_id=tenant_id,
                event_type=CLASS_BOOKING_WAITLISTED_V1,
                payload={
                    "booking_id": str(booking.id),
                    "session_id": str(session.id),
                    "member_id": str(member_id),
                    "waitlist_position": next_pos,
                },
                aggregate_type="class_booking",
                aggregate_id=booking.id,
            )
            return booking

    @staticmethod
    async def cancel_booking(
        db: AsyncSession,
        tenant_id: UUID,
        booking_id: UUID,
        member_id: UUID | None = None,
        reason: str | None = None,
        is_staff: bool = False,
    ) -> ClassBooking:
        """Cancel a booking, enforce cutoff threshold, and auto-promote waitlisted member if applicable."""
        now = datetime.now(UTC)

        # 1. Lock the booking
        b_stmt = (
            select(ClassBooking)
            .where(ClassBooking.tenant_id == tenant_id, ClassBooking.id == booking_id)
            .with_for_update()
        )
        b_res = await db.execute(b_stmt)
        booking = b_res.scalar_one_or_none()

        if not booking:
            raise BookingNotFound("Rezervasyon bulunamadı.")

        if member_id and not is_staff and booking.member_id != member_id:
            raise BookingForbidden("Başka bir üyenin rezervasyonunu iptal edemezsiniz.")

        if booking.status not in [
            ClassBookingStatus.CONFIRMED,
            ClassBookingStatus.WAITLISTED,
        ]:
            raise BookingInvalid(f"Bu rezervasyon zaten {booking.status.value} durumundadır.")

        # 2. Lock the Session
        sess_stmt = (
            select(ClassSession)
            .where(
                ClassSession.tenant_id == tenant_id,
                ClassSession.id == booking.session_id,
            )
            .with_for_update()
        )
        sess_res = await db.execute(sess_stmt)
        session = sess_res.scalar_one()

        # 3. Check cancellation cutoff
        ct_stmt = select(ClassType).where(
            ClassType.tenant_id == tenant_id, ClassType.id == session.class_type_id
        )
        ct_res = await db.execute(ct_stmt)
        class_type = ct_res.scalar_one()

        cutoff = timedelta(minutes=class_type.cancellation_cutoff_minutes)
        is_late = now > (session.start_time_utc - cutoff)

        original_status = booking.status
        cancelled_waitlist_pos = booking.waitlist_position

        booking.status = ClassBookingStatus.CANCELLED
        booking.cancelled_at = now
        booking.cancellation_reason = reason
        booking.is_late_cancellation = is_late
        booking.waitlist_position = None
        await db.flush()

        outbox = OutboxService(db)

        # Emit cancellation event
        await outbox.enqueue(
            tenant_id=tenant_id,
            event_type=CLASS_BOOKING_CANCELLED_V1,
            payload={
                "booking_id": str(booking.id),
                "session_id": str(session.id),
                "member_id": str(booking.member_id),
                "is_late_cancellation": is_late,
            },
            aggregate_type="class_booking",
            aggregate_id=booking.id,
        )

        # 4. If a CONFIRMED booking was cancelled, auto-promote the top waitlisted member
        if original_status == ClassBookingStatus.CONFIRMED:
            top_wait_stmt = (
                select(ClassBooking)
                .where(
                    ClassBooking.tenant_id == tenant_id,
                    ClassBooking.session_id == session.id,
                    ClassBooking.status == ClassBookingStatus.WAITLISTED,
                )
                .order_by(ClassBooking.waitlist_position.asc())
                .limit(1)
                .with_for_update()
            )
            top_wait_res = await db.execute(top_wait_stmt)
            top_wait = top_wait_res.scalar_one_or_none()

            if top_wait:
                # Promote top waitlist to CONFIRMED
                top_wait.status = ClassBookingStatus.CONFIRMED
                top_wait.waitlist_position = None
                await db.flush()

                # Shift all subsequent waitlisted members down by 1
                shift_stmt = (
                    update(ClassBooking)
                    .where(
                        ClassBooking.tenant_id == tenant_id,
                        ClassBooking.session_id == session.id,
                        ClassBooking.status == ClassBookingStatus.WAITLISTED,
                        ClassBooking.waitlist_position > 1,
                    )
                    .values(waitlist_position=ClassBooking.waitlist_position - 1)
                )
                await db.execute(shift_stmt)

                # Emit promotion event
                await outbox.enqueue(
                    tenant_id=tenant_id,
                    event_type=CLASS_BOOKING_PROMOTED_V1,
                    payload={
                        "booking_id": str(top_wait.id),
                        "session_id": str(session.id),
                        "member_id": str(top_wait.member_id),
                    },
                    aggregate_type="class_booking",
                    aggregate_id=top_wait.id,
                )

        elif (
            original_status == ClassBookingStatus.WAITLISTED and cancelled_waitlist_pos
        ):
            # Shift waitlist positions behind the cancelled position down by 1
            shift_stmt = (
                update(ClassBooking)
                .where(
                    ClassBooking.tenant_id == tenant_id,
                    ClassBooking.session_id == session.id,
                    ClassBooking.status == ClassBookingStatus.WAITLISTED,
                    ClassBooking.waitlist_position > cancelled_waitlist_pos,
                )
                .values(waitlist_position=ClassBooking.waitlist_position - 1)
            )
            await db.execute(shift_stmt)

        await db.flush()
        return booking

    @staticmethod
    async def mark_attendance(
        db: AsyncSession,
        tenant_id: UUID,
        booking_id: UUID,
        status_val: ClassBookingStatus,
    ) -> ClassBooking:
        """Mark attendee as ATTENDED or NO_SHOW (trainer / front-desk)."""
        if status_val not in [ClassBookingStatus.ATTENDED, ClassBookingStatus.NO_SHOW]:
            raise BookingInvalid("Geçersiz yoklama durumu.")

        stmt = (
            select(ClassBooking)
            .where(ClassBooking.tenant_id == tenant_id, ClassBooking.id == booking_id)
            .with_for_update()
        )
        res = await db.execute(stmt)
        booking = res.scalar_one_or_none()

        if not booking:
            raise BookingNotFound("Rezervasyon bulunamadı.")
        if booking.status != ClassBookingStatus.CONFIRMED:
            raise BookingConflict("Yalnızca asil listedeki rezervasyon yoklamaya alınır.")

        booking.status = status_val
        if status_val == ClassBookingStatus.ATTENDED:
            booking.attended_at = datetime.now(UTC)
        await db.flush()
        return booking


# ---------------------------------------------------------
# Personal Training (PT) Booking Service
# ---------------------------------------------------------


class PtBookingService:
    """Core domain logic for Trainer Working Hours and 1-on-1 PT Appointments."""

    @staticmethod
    async def create_availability(
        db: AsyncSession, tenant_id: UUID, data: TrainerAvailabilityCreate
    ) -> TrainerAvailability:
        if not await StaffService.has_tenant_role(
            db, tenant_id, data.trainer_user_id, PT_TRAINER_ROLES
        ):
            raise BookingInvalid("Eğitmen bu kulüpte tanımlı değil.")
        if not await StaffService.is_employed(db, tenant_id, data.trainer_user_id):
            raise BookingInvalid("Eğitmen bu kulüpte personel olarak tanımlı değil.")
        avail = TrainerAvailability(
            id=uuid4(),
            tenant_id=tenant_id,
            trainer_user_id=data.trainer_user_id,
            location_id=data.location_id,
            day_of_week=data.day_of_week,
            start_time=data.start_time,
            end_time=data.end_time,
            slot_duration_minutes=data.slot_duration_minutes,
            is_active=data.is_active,
        )
        db.add(avail)
        await db.flush()
        return avail

    @staticmethod
    async def list_availabilities(
        db: AsyncSession,
        tenant_id: UUID,
        trainer_user_id: UUID | None = None,
        location_id: UUID | None = None,
    ) -> list[TrainerAvailability]:
        stmt = select(TrainerAvailability).where(
            TrainerAvailability.tenant_id == tenant_id
        )
        if trainer_user_id:
            stmt = stmt.where(TrainerAvailability.trainer_user_id == trainer_user_id)
        if location_id:
            stmt = stmt.where(TrainerAvailability.location_id == location_id)
        stmt = stmt.where(TrainerAvailability.is_active.is_(True)).order_by(
            TrainerAvailability.day_of_week.asc(), TrainerAvailability.start_time.asc()
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def _require_availability_slot(
        db: AsyncSession,
        tenant_id: UUID,
        trainer_user_id: UUID,
        location_id: UUID,
        start_time_utc: datetime,
        end_time_utc: datetime,
    ) -> None:
        loc = (
            await db.execute(
                select(Location).where(
                    Location.tenant_id == tenant_id, Location.id == location_id
                )
            )
        ).scalar_one_or_none()
        if loc is None:
            raise BookingNotFound("Şube bulunamadı.")
        try:
            loc_tz = ZoneInfo(loc.timezone or "UTC")
        except ZoneInfoNotFoundError as exc:
            raise BookingInvalid("Şube saat dilimi geçersiz.") from exc
        local_start = start_time_utc.astimezone(loc_tz)
        local_end = end_time_utc.astimezone(loc_tz)
        dow = local_start.weekday()
        start_t = local_start.timetz().replace(tzinfo=None)
        end_t = local_end.timetz().replace(tzinfo=None)
        has_hours = (
            await db.execute(
                select(TrainerAvailability.id).where(
                    TrainerAvailability.tenant_id == tenant_id,
                    TrainerAvailability.trainer_user_id == trainer_user_id,
                    TrainerAvailability.location_id == location_id,
                    TrainerAvailability.is_active.is_(True),
                )
            )
        ).first()
        if has_hours is None:
            return
        slot = (
            await db.execute(
                select(TrainerAvailability.id).where(
                    TrainerAvailability.tenant_id == tenant_id,
                    TrainerAvailability.trainer_user_id == trainer_user_id,
                    TrainerAvailability.location_id == location_id,
                    TrainerAvailability.day_of_week == dow,
                    TrainerAvailability.is_active.is_(True),
                    TrainerAvailability.start_time <= start_t,
                    TrainerAvailability.end_time >= end_t,
                )
            )
        ).first()
        if slot is None:
            raise BookingInvalid("Antrenör bu saat aralığında müsait değil.")

    @staticmethod
    async def book_appointment(
        db: AsyncSession,
        tenant_id: UUID,
        trainer_user_id: UUID,
        member_id: UUID,
        location_id: UUID,
        start_time_utc: datetime,
        end_time_utc: datetime,
        notes: str | None = None,
    ) -> PtAppointment:
        """Book a 1-on-1 PT appointment with conflict detection."""
        now = datetime.now(UTC)

        if start_time_utc <= now:
            raise BookingInvalid("Geçmiş saatlere PT randevusu alınamaz.")

        if end_time_utc <= start_time_utc:
            raise BookingInvalid("Bitiş saati başlangıç saatinden sonra olmalıdır.")

        if not await StaffService.has_tenant_role(
            db, tenant_id, trainer_user_id, PT_TRAINER_ROLES
        ):
            raise BookingInvalid("Eğitmen bu kulüpte tanımlı değil.")
        if not await StaffService.is_employed(db, tenant_id, trainer_user_id):
            raise BookingInvalid("Eğitmen bu kulüpte personel olarak tanımlı değil.")
        await PtBookingService._require_availability_slot(
            db, tenant_id, trainer_user_id, location_id, start_time_utc, end_time_utc
        )

        # Check conflicting PT appointment for trainer
        conflict_stmt = (
            select(PtAppointment)
            .where(
                PtAppointment.tenant_id == tenant_id,
                PtAppointment.trainer_user_id == trainer_user_id,
                PtAppointment.status == PtAppointmentStatus.CONFIRMED,
                PtAppointment.start_time_utc < end_time_utc,
                PtAppointment.end_time_utc > start_time_utc,
            )
            .with_for_update()
        )
        conf_res = await db.execute(conflict_stmt)
        if conf_res.scalar_one_or_none():
            raise BookingConflict("Antrenör seçilen saat aralığında doludur.")

        appointment = PtAppointment(
            id=uuid4(),
            tenant_id=tenant_id,
            trainer_user_id=trainer_user_id,
            member_id=member_id,
            location_id=location_id,
            start_time_utc=start_time_utc,
            end_time_utc=end_time_utc,
            status=PtAppointmentStatus.CONFIRMED,
            notes=notes,
            booked_at=now,
        )
        db.add(appointment)
        try:
            await db.flush()
        except IntegrityError as exc:
            raise BookingConflict("Antrenör seçilen saat aralığında doludur.") from exc

        outbox = OutboxService(db)
        await outbox.enqueue(
            tenant_id=tenant_id,
            event_type=PT_APPOINTMENT_CONFIRMED_V1,
            payload={
                "appointment_id": str(appointment.id),
                "trainer_user_id": str(trainer_user_id),
                "member_id": str(member_id),
                "start_time_utc": start_time_utc.isoformat(),
            },
            aggregate_type="pt_appointment",
            aggregate_id=appointment.id,
        )
        return appointment

    @staticmethod
    async def cancel_appointment(
        db: AsyncSession,
        tenant_id: UUID,
        appointment_id: UUID,
        member_id: UUID | None = None,
        is_staff: bool = False,
    ) -> PtAppointment:
        stmt = (
            select(PtAppointment)
            .where(
                PtAppointment.tenant_id == tenant_id, PtAppointment.id == appointment_id
            )
            .with_for_update()
        )
        res = await db.execute(stmt)
        appt = res.scalar_one_or_none()

        if not appt:
            raise BookingNotFound("PT randevusu bulunamadı.")

        if member_id and not is_staff and appt.member_id != member_id:
            raise BookingForbidden("Başka bir üyenin randevusunu iptal edemezsiniz.")

        if appt.status != PtAppointmentStatus.CONFIRMED:
            raise BookingInvalid(f"Randevu zaten {appt.status.value} durumundadır.")

        appt.status = PtAppointmentStatus.CANCELLED
        appt.cancelled_at = datetime.now(UTC)
        await db.flush()

        outbox = OutboxService(db)
        await outbox.enqueue(
            tenant_id=tenant_id,
            event_type=PT_APPOINTMENT_CANCELLED_V1,
            payload={
                "appointment_id": str(appt.id),
                "trainer_user_id": str(appt.trainer_user_id),
                "member_id": str(appt.member_id),
            },
            aggregate_type="pt_appointment",
            aggregate_id=appt.id,
        )
        return appt

    @staticmethod
    async def list_appointments(
        db: AsyncSession,
        tenant_id: UUID,
        trainer_user_id: UUID | None = None,
        member_id: UUID | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[PtAppointment]:
        stmt = select(PtAppointment).where(PtAppointment.tenant_id == tenant_id)
        if trainer_user_id:
            stmt = stmt.where(PtAppointment.trainer_user_id == trainer_user_id)
        if member_id:
            stmt = stmt.where(PtAppointment.member_id == member_id)
        if start_time:
            stmt = stmt.where(PtAppointment.start_time_utc >= start_time)
        if end_time:
            stmt = stmt.where(PtAppointment.start_time_utc <= end_time)
        stmt = stmt.order_by(PtAppointment.start_time_utc.asc())
        res = await db.execute(stmt)
        return list(res.scalars().all())
