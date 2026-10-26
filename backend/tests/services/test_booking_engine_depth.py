"""Service-level booking engine branches not covered by the HTTP suite."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, time, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.booking import (
    ClassBooking,
    ClassBookingStatus,
    ClassSession,
    ClassSessionStatus,
    ClassType,
    PtAppointmentStatus,
)
from app.models.location import Location
from app.models.member import Member
from app.models.organization import Organization
from app.models.rbac import Role, UserRole
from app.models.staff import Staff
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.booking import (
    ClassScheduleCreate,
    ClassScheduleUpdate,
    ClassSessionCreate,
    TrainerAvailabilityCreate,
)
from app.services.booking import (
    BookingConflict,
    BookingForbidden,
    BookingInvalid,
    BookingNotFound,
    ClassBookingService,
    PtBookingService,
)


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Depth Org", domain=f"dep-{uuid4().hex[:8]}.com")
    db_session.add(org)
    await db_session.flush()
    row = Tenant(
        id=uuid4(),
        name="Depth Tenant",
        organization_id=org.id,
        location_code=f"DP-{uuid4().hex[:6]}",
    )
    db_session.add(row)
    await db_session.commit()
    return row


async def _role(db: AsyncSession, name: str) -> Role:
    row = (await db.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
    if row is None:
        row = Role(name=name, description=name)
        db.add(row)
        await db.flush()
    return row


async def _trainer(
    db: AsyncSession, tenant_id, *, employed: bool = True, role_name: str = "TRAINER"
) -> User:
    user = User(
        email=f"tr-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    role = await _role(db, role_name)
    db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant_id))
    if employed:
        db.add(Staff(tenant_id=tenant_id, user_id=user.id, role="TRAINER"))
    await db.flush()
    return user


async def _studio(db: AsyncSession, tenant_id, *, tz: str = "UTC"):
    trainer = await _trainer(db, tenant_id)
    loc = Location(tenant_id=tenant_id, name="Depth Studio", timezone=tz)
    db.add(loc)
    await db.flush()
    class_type = ClassType(
        tenant_id=tenant_id,
        name="Depth Yoga",
        category="MIND",
        duration_minutes=50,
        default_capacity=4,
        cancellation_cutoff_minutes=60,
    )
    db.add(class_type)
    await db.flush()
    return trainer, loc, class_type


async def _member(db: AsyncSession, tenant_id, first: str = "Ada") -> Member:
    member = Member(
        tenant_id=tenant_id,
        member_number=f"M-{uuid4().hex[:6]}",
        first_name=first,
        last_name="Athlete",
        email=f"{first.lower()}-{uuid4().hex[:6]}@example.com",
        status="ACTIVE",
    )
    db.add(member)
    await db.flush()
    return member


async def _session(
    db: AsyncSession,
    tenant_id,
    *,
    trainer_id,
    location_id,
    class_type_id,
    start: datetime | None = None,
    capacity: int = 4,
    status: ClassSessionStatus = ClassSessionStatus.SCHEDULED,
    schedule_id=None,
) -> ClassSession:
    start = start or (datetime.now(UTC) + timedelta(days=2))
    sess = ClassSession(
        tenant_id=tenant_id,
        location_id=location_id,
        class_type_id=class_type_id,
        schedule_id=schedule_id,
        trainer_user_id=trainer_id,
        start_time_utc=start,
        end_time_utc=start + timedelta(minutes=50),
        room_name="A",
        capacity=capacity,
        status=status,
    )
    db.add(sess)
    await db.flush()
    return sess


@pytest.mark.asyncio
async def test_schedule_generation_overnight_duplicate_and_invalid_tz(
    db_session, tenant
):
    trainer, loc, class_type = await _studio(db_session, tenant.id)
    monday = datetime(2026, 8, 17, tzinfo=UTC)  # Monday
    created = await ClassBookingService.create_schedule(
        db_session,
        tenant.id,
        ClassScheduleCreate(
            location_id=loc.id,
            class_type_id=class_type.id,
            trainer_user_id=trainer.id,
            day_of_week=0,
            start_time=time(23, 0),
            end_time=time(1, 0),
            room_name="Night",
            capacity=8,
        ),
    )
    await db_session.commit()

    listed = await ClassBookingService.list_schedules(
        db_session, tenant.id, location_id=loc.id
    )
    assert [row.id for row in listed] == [created.id]

    updated = await ClassBookingService.update_schedule(
        db_session,
        tenant.id,
        created.id,
        ClassScheduleUpdate(room_name="Night Hall"),
    )
    assert updated.room_name == "Night Hall"

    first = await ClassBookingService.generate_sessions_from_schedule(
        db_session,
        tenant.id,
        created.id,
        monday,
        monday + timedelta(days=1),
    )
    assert len(first) == 1
    assert first[0].end_time_utc - first[0].start_time_utc == timedelta(hours=2)

    again = await ClassBookingService.generate_sessions_from_schedule(
        db_session,
        tenant.id,
        created.id,
        monday,
        monday + timedelta(days=1),
    )
    assert again == []

    by_schedule = await ClassBookingService.list_sessions(
        db_session, tenant.id, schedule_id=created.id
    )
    assert len(by_schedule) == 1

    loc.timezone = "Not/ARealZone"
    await db_session.flush()
    with pytest.raises(BookingInvalid, match="saat dilimi"):
        await ClassBookingService.generate_sessions_from_schedule(
            db_session,
            tenant.id,
            created.id,
            monday + timedelta(days=7),
            monday + timedelta(days=8),
        )

    created.is_active = False
    await db_session.flush()
    with pytest.raises(BookingNotFound, match="Aktif ders programı"):
        await ClassBookingService.generate_sessions_from_schedule(
            db_session, tenant.id, created.id, monday, monday + timedelta(days=1)
        )


@pytest.mark.asyncio
async def test_trainer_gate_on_schedule_session_and_availability(db_session, tenant):
    _, loc, class_type = await _studio(db_session, tenant.id)
    stranger = User(
        email=f"str-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db_session.add(stranger)
    await db_session.flush()
    jobless = await _trainer(db_session, tenant.id, employed=False)
    await db_session.commit()

    payload = ClassScheduleCreate(
        location_id=loc.id,
        class_type_id=class_type.id,
        trainer_user_id=stranger.id,
        day_of_week=1,
        start_time=time(10, 0),
        end_time=time(11, 0),
        capacity=6,
    )
    with pytest.raises(BookingInvalid, match="tanımlı değil"):
        await ClassBookingService.create_schedule(db_session, tenant.id, payload)

    payload.trainer_user_id = jobless.id
    with pytest.raises(BookingInvalid, match="personel"):
        await ClassBookingService.create_schedule(db_session, tenant.id, payload)

    start = datetime.now(UTC) + timedelta(days=4)
    session_data = ClassSessionCreate(
        location_id=loc.id,
        class_type_id=class_type.id,
        trainer_user_id=stranger.id,
        start_time_utc=start,
        end_time_utc=start + timedelta(minutes=50),
        capacity=6,
    )
    with pytest.raises(BookingInvalid, match="tanımlı değil"):
        await ClassBookingService.create_session(db_session, tenant.id, session_data)

    avail = TrainerAvailabilityCreate(
        trainer_user_id=stranger.id,
        location_id=loc.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    with pytest.raises(BookingInvalid, match="tanımlı değil"):
        await PtBookingService.create_availability(db_session, tenant.id, avail)

    avail.trainer_user_id = jobless.id
    with pytest.raises(BookingInvalid, match="personel"):
        await PtBookingService.create_availability(db_session, tenant.id, avail)


@pytest.mark.asyncio
async def test_create_session_roster_and_book_error_paths(db_session, tenant):
    trainer, loc, class_type = await _studio(db_session, tenant.id)
    start = datetime.now(UTC) + timedelta(days=5)
    created = await ClassBookingService.create_session(
        db_session,
        tenant.id,
        ClassSessionCreate(
            location_id=loc.id,
            class_type_id=class_type.id,
            trainer_user_id=trainer.id,
            start_time_utc=start,
            end_time_utc=start + timedelta(minutes=50),
            room_name="B",
            capacity=1,
        ),
    )
    member = await _member(db_session, tenant.id)
    waiter = await _member(db_session, tenant.id, first="Wait")
    no_show = await _member(db_session, tenant.id, first="NoShow")
    booked = await ClassBookingService.book_session(
        db_session, tenant.id, created.id, member.id
    )
    waitlisted = await ClassBookingService.book_session(
        db_session, tenant.id, created.id, waiter.id
    )
    assert booked.status == ClassBookingStatus.CONFIRMED
    assert waitlisted.status == ClassBookingStatus.WAITLISTED
    assert waitlisted.waitlist_position == 1

    extra = ClassBooking(
        tenant_id=tenant.id,
        session_id=created.id,
        member_id=no_show.id,
        status=ClassBookingStatus.NO_SHOW,
        booked_at=datetime.now(UTC),
    )
    db_session.add(extra)
    await db_session.flush()

    roster = await ClassBookingService.get_session_roster(
        db_session, tenant.id, created.id
    )
    assert roster.session.id == created.id
    assert roster.total_confirmed == 2
    assert roster.total_waitlisted == 1
    assert {a.member_id for a in roster.attendees} == {
        member.id,
        waiter.id,
        no_show.id,
    }

    with pytest.raises(BookingNotFound, match="seansı"):
        await ClassBookingService.get_session_roster(db_session, tenant.id, uuid4())

    with pytest.raises(BookingInvalid, match="aktif rezervasyon"):
        await ClassBookingService.book_session(
            db_session, tenant.id, created.id, member.id
        )

    missing = await _session(
        db_session,
        tenant.id,
        trainer_id=trainer.id,
        location_id=loc.id,
        class_type_id=class_type.id,
        status=ClassSessionStatus.CANCELLED,
    )
    with pytest.raises(BookingInvalid, match="kapalı"):
        await ClassBookingService.book_session(
            db_session, tenant.id, missing.id, member.id
        )

    past = await _session(
        db_session,
        tenant.id,
        trainer_id=trainer.id,
        location_id=loc.id,
        class_type_id=class_type.id,
        start=datetime.now(UTC) - timedelta(hours=1),
    )
    with pytest.raises(BookingInvalid, match="Geçmiş"):
        await ClassBookingService.book_session(
            db_session,
            tenant.id,
            past.id,
            (await _member(db_session, tenant.id, "Past")).id,
        )

    with pytest.raises(BookingNotFound, match="seansı"):
        await ClassBookingService.book_session(
            db_session, tenant.id, uuid4(), member.id
        )


@pytest.mark.asyncio
async def test_book_requires_entitlement_and_skips_broke_waitlist(db_session, tenant):
    trainer, loc, class_type = await _studio(db_session, tenant.id)
    class_type.required_entitlement_type = "CLASS_GROUP"
    await db_session.flush()
    sess = await _session(
        db_session,
        tenant.id,
        trainer_id=trainer.id,
        location_id=loc.id,
        class_type_id=class_type.id,
        capacity=1,
    )
    broke = await _member(db_session, tenant.id, first="Broke")
    with pytest.raises(BookingForbidden, match="hakkınız"):
        await ClassBookingService.book_session(db_session, tenant.id, sess.id, broke.id)

    holder = await _member(db_session, tenant.id, first="Holder")
    waiter = await _member(db_session, tenant.id, first="Queued")
    confirmed = ClassBooking(
        tenant_id=tenant.id,
        session_id=sess.id,
        member_id=holder.id,
        status=ClassBookingStatus.CONFIRMED,
        booked_at=datetime.now(UTC),
    )
    queued = ClassBooking(
        tenant_id=tenant.id,
        session_id=sess.id,
        member_id=waiter.id,
        status=ClassBookingStatus.WAITLISTED,
        waitlist_position=1,
        booked_at=datetime.now(UTC),
    )
    db_session.add_all([confirmed, queued])
    await db_session.commit()

    cancelled = await ClassBookingService.cancel_booking(
        db_session, tenant.id, confirmed.id, member_id=holder.id
    )
    assert cancelled.status == ClassBookingStatus.CANCELLED
    await db_session.refresh(queued)
    assert queued.status == ClassBookingStatus.WAITLISTED
    assert queued.waitlist_position == 1


@pytest.mark.asyncio
async def test_book_consume_access_race_is_forbidden(db_session, tenant):
    trainer, loc, class_type = await _studio(db_session, tenant.id)
    class_type.required_entitlement_type = "CLASS_GROUP"
    await db_session.flush()
    sess = await _session(
        db_session,
        tenant.id,
        trainer_id=trainer.id,
        location_id=loc.id,
        class_type_id=class_type.id,
    )
    member = await _member(db_session, tenant.id)
    with (
        patch(
            "app.services.booking.EntitlementService.check_access",
            new=AsyncMock(return_value={"granted": True}),
        ),
        patch(
            "app.services.booking.EntitlementService.consume_access",
            new=AsyncMock(return_value={"granted": False}),
        ),
        pytest.raises(BookingForbidden, match="hakkınız"),
    ):
        await ClassBookingService.book_session(
            db_session, tenant.id, sess.id, member.id
        )


@pytest.mark.asyncio
async def test_mark_attendance_paths(db_session, tenant):
    trainer, loc, class_type = await _studio(db_session, tenant.id)
    sess = await _session(
        db_session,
        tenant.id,
        trainer_id=trainer.id,
        location_id=loc.id,
        class_type_id=class_type.id,
    )
    member = await _member(db_session, tenant.id)
    waiter = await _member(db_session, tenant.id, first="Wait")
    booking = await ClassBookingService.book_session(
        db_session, tenant.id, sess.id, member.id
    )
    waitlisted = ClassBooking(
        tenant_id=tenant.id,
        session_id=sess.id,
        member_id=waiter.id,
        status=ClassBookingStatus.WAITLISTED,
        waitlist_position=1,
        booked_at=datetime.now(UTC),
    )
    db_session.add(waitlisted)
    await db_session.flush()

    with pytest.raises(BookingInvalid, match="yoklama"):
        await ClassBookingService.mark_attendance(
            db_session, tenant.id, booking.id, ClassBookingStatus.CANCELLED
        )
    with pytest.raises(BookingNotFound):
        await ClassBookingService.mark_attendance(
            db_session, tenant.id, uuid4(), ClassBookingStatus.ATTENDED
        )
    with pytest.raises(BookingConflict, match="asil"):
        await ClassBookingService.mark_attendance(
            db_session, tenant.id, waitlisted.id, ClassBookingStatus.NO_SHOW
        )

    attended = await ClassBookingService.mark_attendance(
        db_session, tenant.id, booking.id, ClassBookingStatus.ATTENDED
    )
    assert attended.status == ClassBookingStatus.ATTENDED
    assert attended.attended_at is not None

    other = await ClassBookingService.book_session(
        db_session,
        tenant.id,
        (
            await _session(
                db_session,
                tenant.id,
                trainer_id=trainer.id,
                location_id=loc.id,
                class_type_id=class_type.id,
                start=datetime.now(UTC) + timedelta(days=6),
            )
        ).id,
        waiter.id,
    )
    noshow = await ClassBookingService.mark_attendance(
        db_session, tenant.id, other.id, ClassBookingStatus.NO_SHOW
    )
    assert noshow.status == ClassBookingStatus.NO_SHOW
    assert noshow.attended_at is None


@pytest.mark.asyncio
async def test_pt_availability_slot_and_appointment_paths(db_session, tenant):
    trainer, loc, _class_type = await _studio(db_session, tenant.id)
    member = await _member(db_session, tenant.id)
    other = await _member(db_session, tenant.id, first="Other")
    await db_session.commit()

    empty = await PtBookingService.list_availabilities(db_session, tenant.id)
    assert empty == []

    avail = await PtBookingService.create_availability(
        db_session,
        tenant.id,
        TrainerAvailabilityCreate(
            trainer_user_id=trainer.id,
            location_id=loc.id,
            day_of_week=0,
            start_time=time(10, 0),
            end_time=time(18, 0),
            slot_duration_minutes=60,
        ),
    )
    listed = await PtBookingService.list_availabilities(
        db_session, tenant.id, trainer_user_id=trainer.id, location_id=loc.id
    )
    assert [row.id for row in listed] == [avail.id]
    assert (
        await PtBookingService.list_availabilities(
            db_session, tenant.id, location_id=uuid4()
        )
        == []
    )

    monday = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
    tuesday = datetime(2026, 8, 25, 10, 0, tzinfo=UTC)
    booked = await PtBookingService.book_appointment(
        db_session,
        tenant.id,
        trainer.id,
        member.id,
        loc.id,
        monday,
        monday + timedelta(hours=1),
        notes="legs",
    )
    assert booked.status == PtAppointmentStatus.CONFIRMED

    with pytest.raises(BookingInvalid, match="müsait değil"):
        await PtBookingService.book_appointment(
            db_session,
            tenant.id,
            trainer.id,
            other.id,
            loc.id,
            tuesday,
            tuesday + timedelta(hours=1),
        )
    with pytest.raises(BookingInvalid, match="müsait değil"):
        await PtBookingService.book_appointment(
            db_session,
            tenant.id,
            trainer.id,
            other.id,
            loc.id,
            monday.replace(hour=19),
            monday.replace(hour=20),
        )
    with pytest.raises(BookingInvalid, match="Geçmiş"):
        await PtBookingService.book_appointment(
            db_session,
            tenant.id,
            trainer.id,
            other.id,
            loc.id,
            datetime.now(UTC) - timedelta(hours=1),
            datetime.now(UTC),
        )
    with pytest.raises(BookingInvalid, match="Bitiş"):
        await PtBookingService.book_appointment(
            db_session,
            tenant.id,
            trainer.id,
            other.id,
            loc.id,
            monday + timedelta(days=14),
            monday + timedelta(days=14),
        )
    with pytest.raises(BookingNotFound, match="Şube"):
        await PtBookingService.book_appointment(
            db_session,
            tenant.id,
            trainer.id,
            other.id,
            uuid4(),
            monday + timedelta(days=14),
            monday + timedelta(days=14, hours=1),
        )

    loc.timezone = "Not/ARealZone"
    await db_session.flush()
    with pytest.raises(BookingInvalid, match="saat dilimi"):
        await PtBookingService.book_appointment(
            db_session,
            tenant.id,
            trainer.id,
            other.id,
            loc.id,
            monday + timedelta(days=21),
            monday + timedelta(days=21, hours=1),
        )
    loc.timezone = "UTC"
    await db_session.flush()

    stranger = User(
        email=f"notr-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db_session.add(stranger)
    await db_session.flush()
    with pytest.raises(BookingInvalid, match="tanımlı değil"):
        await PtBookingService.book_appointment(
            db_session,
            tenant.id,
            stranger.id,
            other.id,
            loc.id,
            monday + timedelta(days=28),
            monday + timedelta(days=28, hours=1),
        )

    listed_appts = await PtBookingService.list_appointments(
        db_session,
        tenant.id,
        trainer_user_id=trainer.id,
        member_id=member.id,
        start_time=monday - timedelta(hours=1),
        end_time=monday + timedelta(hours=2),
    )
    assert [row.id for row in listed_appts] == [booked.id]
    assert (
        await PtBookingService.list_appointments(
            db_session, tenant.id, member_id=other.id
        )
        == []
    )

    with pytest.raises(BookingNotFound):
        await PtBookingService.cancel_appointment(db_session, tenant.id, uuid4())
    with pytest.raises(BookingForbidden):
        await PtBookingService.cancel_appointment(
            db_session, tenant.id, booked.id, member_id=other.id, is_staff=False
        )
    cancelled = await PtBookingService.cancel_appointment(
        db_session, tenant.id, booked.id, member_id=member.id
    )
    assert cancelled.status == PtAppointmentStatus.CANCELLED
    with pytest.raises(BookingInvalid, match="zaten"):
        await PtBookingService.cancel_appointment(
            db_session, tenant.id, booked.id, member_id=member.id
        )

    later_start = monday + timedelta(days=35)
    staff_ok = await PtBookingService.book_appointment(
        db_session,
        tenant.id,
        trainer.id,
        other.id,
        loc.id,
        later_start.replace(hour=11, minute=0, second=0, microsecond=0),
        later_start.replace(hour=12, minute=0, second=0, microsecond=0),
    )
    staff_cancel = await PtBookingService.cancel_appointment(
        db_session,
        tenant.id,
        staff_ok.id,
        member_id=member.id,
        is_staff=True,
    )
    assert staff_cancel.status == PtAppointmentStatus.CANCELLED


@pytest.mark.asyncio
async def test_pt_books_when_trainer_has_no_hours_defined(db_session, tenant):
    trainer, loc, _class_type = await _studio(db_session, tenant.id)
    member = await _member(db_session, tenant.id)
    start = datetime.now(UTC) + timedelta(days=9)
    appt = await PtBookingService.book_appointment(
        db_session,
        tenant.id,
        trainer.id,
        member.id,
        loc.id,
        start,
        start + timedelta(hours=1),
    )
    assert appt.status == PtAppointmentStatus.CONFIRMED


@pytest.mark.asyncio
async def test_update_schedule_rejects_invalid_trainer_swap(db_session, tenant):
    trainer, loc, class_type = await _studio(db_session, tenant.id)
    schedule = await ClassBookingService.create_schedule(
        db_session,
        tenant.id,
        ClassScheduleCreate(
            location_id=loc.id,
            class_type_id=class_type.id,
            trainer_user_id=trainer.id,
            day_of_week=3,
            start_time=time(12, 0),
            end_time=time(13, 0),
            capacity=5,
        ),
    )
    stranger = User(
        email=f"swap-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db_session.add(stranger)
    await db_session.flush()
    with pytest.raises(BookingInvalid, match="tanımlı değil"):
        await ClassBookingService.update_schedule(
            db_session,
            tenant.id,
            schedule.id,
            ClassScheduleUpdate(trainer_user_id=stranger.id),
        )
    replacement = await _trainer(db_session, tenant.id)
    swapped = await ClassBookingService.update_schedule(
        db_session,
        tenant.id,
        schedule.id,
        ClassScheduleUpdate(trainer_user_id=replacement.id),
    )
    assert swapped.trainer_user_id == replacement.id
