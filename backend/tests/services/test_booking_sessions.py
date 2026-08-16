"""Service-level list_sessions filters and cancel_booking error paths."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.booking import (
    ClassBooking,
    ClassBookingStatus,
    ClassSession,
    ClassSessionStatus,
    ClassType,
)
from app.models.location import Location
from app.models.member import Member
from app.models.organization import Organization
from app.models.staff import Staff
from app.models.tenant import Tenant
from app.models.user import User
from app.services.booking import (
    BookingForbidden,
    BookingInvalid,
    BookingNotFound,
    ClassBookingService,
)


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Sess Org", domain=f"ss-{uuid4().hex[:8]}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="Sess Tenant",
        organization_id=org.id,
        location_code=f"SS-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


async def _studio(db: AsyncSession, tenant_id):
    trainer = User(
        email=f"tr-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(trainer)
    await db.flush()
    loc = Location(tenant_id=tenant_id, name="Main Studio", timezone="UTC")
    db.add(loc)
    await db.flush()
    db.add(Staff(tenant_id=tenant_id, user_id=trainer.id, role="TRAINER"))
    class_type = ClassType(
        tenant_id=tenant_id,
        name="Yoga",
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
) -> ClassSession:
    start = start or (datetime.now(UTC) + timedelta(days=2))
    sess = ClassSession(
        tenant_id=tenant_id,
        location_id=location_id,
        class_type_id=class_type_id,
        trainer_user_id=trainer_id,
        start_time_utc=start,
        end_time_utc=start + timedelta(minutes=50),
        room_name="A",
        capacity=capacity,
        status=ClassSessionStatus.SCHEDULED,
    )
    db.add(sess)
    await db.flush()
    return sess


async def _booking(
    db: AsyncSession,
    tenant_id,
    session_id,
    member_id,
    status: ClassBookingStatus = ClassBookingStatus.CONFIRMED,
    waitlist_position: int | None = None,
) -> ClassBooking:
    row = ClassBooking(
        tenant_id=tenant_id,
        session_id=session_id,
        member_id=member_id,
        status=status,
        waitlist_position=waitlist_position,
        booked_at=datetime.now(UTC),
    )
    db.add(row)
    await db.flush()
    return row


@pytest.mark.asyncio
async def test_list_sessions_empty_and_filters(db_session, tenant):
    empty = await ClassBookingService.list_sessions(db_session, tenant.id)
    assert empty == []

    trainer, loc, class_type = await _studio(db_session, tenant.id)
    start = datetime.now(UTC) + timedelta(days=3)
    sess = await _session(
        db_session,
        tenant.id,
        trainer_id=trainer.id,
        location_id=loc.id,
        class_type_id=class_type.id,
        start=start,
        capacity=2,
    )
    member = await _member(db_session, tenant.id)
    waiter = await _member(db_session, tenant.id, first="Wait")
    confirmed = await _booking(db_session, tenant.id, sess.id, member.id)
    await _booking(
        db_session,
        tenant.id,
        sess.id,
        waiter.id,
        status=ClassBookingStatus.WAITLISTED,
        waitlist_position=1,
    )
    await db_session.commit()

    listed = await ClassBookingService.list_sessions(db_session, tenant.id)
    assert len(listed) == 1
    row = listed[0]
    assert row.id == sess.id
    assert row.class_type_name == "Yoga"
    assert row.location_name == "Main Studio"
    assert row.trainer_name == trainer.email
    assert row.confirmed_count == 1
    assert row.waitlist_count == 1
    assert row.available_spots == 1
    assert row.user_booking_status is None

    mine = await ClassBookingService.list_sessions(
        db_session, tenant.id, member_id=member.id
    )
    assert mine[0].user_booking_id == confirmed.id
    assert mine[0].user_booking_status == ClassBookingStatus.CONFIRMED
    assert mine[0].user_waitlist_position is None

    wait_view = await ClassBookingService.list_sessions(
        db_session, tenant.id, member_id=waiter.id
    )
    assert wait_view[0].user_booking_status == ClassBookingStatus.WAITLISTED
    assert wait_view[0].user_waitlist_position == 1

    assert (
        await ClassBookingService.list_sessions(
            db_session, tenant.id, location_id=loc.id
        )
    )[0].id == sess.id
    assert (
        await ClassBookingService.list_sessions(
            db_session, tenant.id, class_type_id=class_type.id
        )
    )[0].id == sess.id
    assert (
        await ClassBookingService.list_sessions(
            db_session, tenant.id, trainer_user_id=trainer.id
        )
    )[0].id == sess.id
    assert (
        await ClassBookingService.list_sessions(
            db_session, tenant.id, session_id=sess.id
        )
    )[0].id == sess.id
    assert (
        await ClassBookingService.list_sessions(
            db_session,
            tenant.id,
            start_time=start - timedelta(hours=1),
            end_time=start + timedelta(hours=1),
        )
    )[0].id == sess.id
    assert (
        await ClassBookingService.list_sessions(
            db_session, tenant.id, location_id=uuid4()
        )
        == []
    )
    assert (
        await ClassBookingService.list_sessions(
            db_session, tenant.id, start_time=start + timedelta(days=1)
        )
        == []
    )


@pytest.mark.asyncio
async def test_cancel_booking_error_paths_and_waitlist_shift(db_session, tenant):
    trainer, loc, class_type = await _studio(db_session, tenant.id)
    sess = await _session(
        db_session,
        tenant.id,
        trainer_id=trainer.id,
        location_id=loc.id,
        class_type_id=class_type.id,
        capacity=2,
    )
    owner = await _member(db_session, tenant.id, first="Owner")
    other = await _member(db_session, tenant.id, first="Other")
    wait_a = await _member(db_session, tenant.id, first="WaitA")
    wait_b = await _member(db_session, tenant.id, first="WaitB")
    confirmed = await _booking(db_session, tenant.id, sess.id, owner.id)
    waitlisted = await _booking(
        db_session,
        tenant.id,
        sess.id,
        wait_a.id,
        status=ClassBookingStatus.WAITLISTED,
        waitlist_position=1,
    )
    behind = await _booking(
        db_session,
        tenant.id,
        sess.id,
        wait_b.id,
        status=ClassBookingStatus.WAITLISTED,
        waitlist_position=2,
    )
    await db_session.commit()

    with pytest.raises(BookingNotFound):
        await ClassBookingService.cancel_booking(
            db_session, tenant.id, uuid4(), member_id=owner.id
        )

    with pytest.raises(BookingForbidden):
        await ClassBookingService.cancel_booking(
            db_session,
            tenant.id,
            confirmed.id,
            member_id=other.id,
            is_staff=False,
        )

    cancelled_wait = await ClassBookingService.cancel_booking(
        db_session,
        tenant.id,
        waitlisted.id,
        member_id=wait_a.id,
        reason="changed_mind",
    )
    assert cancelled_wait.status == ClassBookingStatus.CANCELLED
    await db_session.refresh(behind)
    await db_session.refresh(confirmed)
    assert behind.status == ClassBookingStatus.WAITLISTED
    assert behind.waitlist_position == 1
    assert confirmed.status == ClassBookingStatus.CONFIRMED

    staff_ok = await ClassBookingService.cancel_booking(
        db_session,
        tenant.id,
        confirmed.id,
        member_id=other.id,
        reason="desk",
        is_staff=True,
    )
    assert staff_ok.status == ClassBookingStatus.CANCELLED

    with pytest.raises(BookingInvalid):
        await ClassBookingService.cancel_booking(
            db_session, tenant.id, confirmed.id, member_id=owner.id
        )
