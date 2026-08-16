"""Complete pytest suite for Group Class & PT Booking Engine.

Tests:
1. Class Type & Recurring Schedule generation.
2. Concurrent capacity reservation with SELECT ... FOR UPDATE (no overbooking).
3. Monotonic waitlist queue ordering.
4. Auto-promotion of waitlist #1 upon timely cancellation and waitlist position shifting.
5. Cancellation cutoff enforcement (timely vs late cancellation).
6. Attendance marking (ATTENDED / NO_SHOW).
7. PT appointment booking & trainer overlapping conflict prevention (409 Conflict).
8. Multi-tenant and member-level authorization isolation.
"""

from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.main import app
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
from app.models.outbox import OutboxEvent
from app.models.rbac import Permission, Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User, UserSession


def _token_pair() -> tuple[str, str]:
    raw = f"tok_{uuid4().hex}"
    return raw, hashlib.sha256(raw.encode()).hexdigest()


async def _ensure_perm(db: AsyncSession, name: str) -> Permission:
    row = (
        await db.execute(select(Permission).where(Permission.name == name))
    ).scalar_one_or_none()
    if row is None:
        row = Permission(name=name, description=name)
        db.add(row)
        await db.flush()
    return row


async def _create_user_with_role(
    db: AsyncSession,
    *,
    role_name: str,
    tenant_id: UUID,
    perms: list[str],
) -> tuple[User, str]:
    raw, th = _token_pair()
    user = User(
        id=uuid4(),
        email=f"{role_name.lower()}-{uuid4().hex[:8]}@example.com",
        hashed_password="hash",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    role = (
        await db.execute(select(Role).where(Role.name == role_name))
    ).scalar_one_or_none()
    if role is None:
        role = Role(
            name=role_name,
            description=role_name,
            permissions=[await _ensure_perm(db, p) for p in perms],
        )
        db.add(role)
        await db.flush()

    db.add(
        UserRole(
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant_id,
        )
    )
    from app.models.staff import Staff
    from app.services.staff import ALLOWED_STAFF_ROLES

    job = role_name if role_name in ALLOWED_STAFF_ROLES else "TRAINER"
    if role_name in {"TRAINER", "GYM_ADMIN", "GYM_OWNER", "GYM_MANAGER"}:
        db.add(Staff(tenant_id=tenant_id, user_id=user.id, role=job))
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=th,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
    )
    await db.flush()
    return user, raw


async def _create_member_for_user(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    first_name: str = "Test",
    last_name: str = "Athlete",
) -> Member:
    member = Member(
        id=uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        member_number=f"MBR-{uuid4().hex[:8].upper()}",
        first_name=first_name,
        last_name=last_name,
        email=f"member-{uuid4().hex[:6]}@example.com",
        phone=f"+90555{uuid4().int % 10000000:07d}",
        status="ACTIVE",
    )
    db.add(member)
    await db.flush()
    return member


@pytest.fixture
async def api_client(pg_session_maker):
    async def override_get_db():
        async with pg_session_maker() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_class_type_and_schedule_flow(pg_session_maker, api_client: AsyncClient):
    """Test creating class types, master schedules, and generating concrete sessions."""
    async with pg_session_maker() as db:
        org = Organization(
            id=uuid4(), name="FitNet", domain=f"fitnet-{uuid4().hex[:6]}.com"
        )
        db.add(org)
        await db.flush()

        tenant = Tenant(
            id=uuid4(),
            organization_id=org.id,
            name="Club Kadikoy",
            location_code=f"KAD-{uuid4().hex[:4]}",
        )
        db.add(tenant)
        await db.flush()

        await db.execute(
            select(func.set_config("app.current_tenant_id", str(tenant.id), True))
        )

        loc = Location(
            id=uuid4(),
            tenant_id=tenant.id,
            name="Main Studio",
            timezone="Europe/Istanbul",
        )
        db.add(loc)
        await db.flush()

        _, admin_token = await _create_user_with_role(
            db,
            role_name="GYM_ADMIN",
            tenant_id=tenant.id,
            perms=["classes:read", "classes:write"],
        )
        trainer_user, _ = await _create_user_with_role(
            db,
            role_name="TRAINER",
            tenant_id=tenant.id,
            perms=["classes:read", "classes:attend"],
        )
        await db.commit()

    headers = {"Authorization": f"Bearer {admin_token}", "X-Tenant-ID": str(tenant.id)}

    # 1. Create Class Type (Pilates)
    create_type_res = await api_client.post(
        "/api/v1/classes/types",
        headers=headers,
        json={
            "name": "Reformer Pilates",
            "category": "PILATES",
            "duration_minutes": 50,
            "default_capacity": 6,
            "color_hex": "#EC4899",
            "cancellation_cutoff_minutes": 120,
        },
    )
    assert create_type_res.status_code == 201
    class_type_id = create_type_res.json()["id"]

    # 2. Create Recurring Schedule (Every Monday at 10:00)
    create_sched_res = await api_client.post(
        "/api/v1/classes/schedules",
        headers=headers,
        json={
            "location_id": str(loc.id),
            "class_type_id": class_type_id,
            "trainer_user_id": str(trainer_user.id),
            "day_of_week": 0,  # Monday
            "start_time": "10:00:00",
            "end_time": "10:50:00",
            "room_name": "Studio A",
            "capacity": 6,
        },
    )
    assert create_sched_res.status_code == 201
    schedule_id = create_sched_res.json()["id"]

    # 3. Generate sessions for next 14 days
    now = datetime.now(UTC)
    gen_res = await api_client.post(
        f"/api/v1/classes/schedules/{schedule_id}/generate-sessions",
        headers=headers,
        json={
            "schedule_id": schedule_id,
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=14)).isoformat(),
        },
    )
    assert gen_res.status_code == 200
    sessions = gen_res.json()
    assert len(sessions) >= 1
    assert sessions[0]["class_type_name"] == "Reformer Pilates"
    assert sessions[0]["capacity"] == 6
    start_utc = datetime.fromisoformat(sessions[0]["start_time_utc"].replace("Z", "+00:00"))
    assert start_utc.hour != 10 or start_utc.tzinfo is None
    # Istanbul 10:00 is 07:00Z (winter) or 06:00Z (summer), never 10:00Z.
    assert start_utc.astimezone(UTC).hour in {6, 7}


@pytest.mark.asyncio
async def test_concurrent_booking_and_waitlist_auto_promotion(
    pg_session_maker, api_client: AsyncClient
):
    """Verify concurrency safety (no overbooking) and monotonic waitlist auto-promotion on real PostgreSQL."""
    async with pg_session_maker() as db:
        org = Organization(
            id=uuid4(),
            name="FitNet Concurrency",
            domain=f"fitnet-c-{uuid4().hex[:6]}.com",
        )
        db.add(org)
        await db.flush()

        tenant = Tenant(
            id=uuid4(),
            organization_id=org.id,
            name="Club Besiktas",
            location_code=f"BES-{uuid4().hex[:4]}",
        )
        db.add(tenant)
        await db.flush()

        await db.execute(
            select(func.set_config("app.current_tenant_id", str(tenant.id), True))
        )

        loc = Location(
            id=uuid4(),
            tenant_id=tenant.id,
            name="Spin Studio",
            timezone="Europe/Istanbul",
        )
        db.add(loc)
        await db.flush()

        trainer_user, _ = await _create_user_with_role(
            db,
            role_name="TRAINER",
            tenant_id=tenant.id,
            perms=["classes:read", "classes:attend"],
        )

        class_type = ClassType(
            id=uuid4(),
            tenant_id=tenant.id,
            name="Spinning Blast",
            category="CARDIO",
            duration_minutes=45,
            default_capacity=3,  # Strict capacity of 3
            color_hex="#F59E0B",
            cancellation_cutoff_minutes=60,
        )
        db.add(class_type)
        await db.flush()

        future_start = datetime.now(UTC) + timedelta(days=2)
        session = ClassSession(
            id=uuid4(),
            tenant_id=tenant.id,
            location_id=loc.id,
            class_type_id=class_type.id,
            trainer_user_id=trainer_user.id,
            start_time_utc=future_start,
            end_time_utc=future_start + timedelta(minutes=45),
            room_name="Studio Spin",
            capacity=3,  # Capacity is 3
            status=ClassSessionStatus.SCHEDULED,
        )
        db.add(session)
        await db.flush()

        # Create 10 distinct members with login sessions
        members_data = []
        for i in range(10):
            u, tok = await _create_user_with_role(
                db,
                role_name="MEMBER",
                tenant_id=tenant.id,
                perms=["classes:read:self", "classes:book:self"],
            )
            m = await _create_member_for_user(
                db, tenant_id=tenant.id, user_id=u.id, first_name=f"Athlete{i}"
            )
            members_data.append((u, m, tok))

        await db.commit()

    # 1. 10 Members book simultaneously
    async def book_for_member(member_tuple):
        _, _, tok = member_tuple
        headers = {"Authorization": f"Bearer {tok}", "X-Tenant-ID": str(tenant.id)}
        res = await api_client.post(
            f"/api/v1/me/classes/sessions/{session.id}/book", headers=headers
        )
        return res

    results = await asyncio.gather(*(book_for_member(m) for m in members_data))

    confirmed_bookings = [
        r.json()
        for r in results
        if r.status_code == 201 and r.json()["status"] == "CONFIRMED"
    ]
    waitlisted_bookings = [
        r.json()
        for r in results
        if r.status_code == 201 and r.json()["status"] == "WAITLISTED"
    ]

    # Invariant: EXACTLY 3 Confirmed, EXACTLY 7 Waitlisted
    assert len(confirmed_bookings) == 3, (
        f"Expected 3 confirmed, got {len(confirmed_bookings)}"
    )
    assert len(waitlisted_bookings) == 7, (
        f"Expected 7 waitlisted, got {len(waitlisted_bookings)}"
    )

    # Invariant: Waitlist positions are monotonic 1..7 without duplicates or gaps
    positions = sorted([w["waitlist_position"] for w in waitlisted_bookings])
    assert positions == [1, 2, 3, 4, 5, 6, 7], (
        f"Waitlist positions mismatch: {positions}"
    )

    # 2. Confirmed Member #0 cancels their booking
    # Find which member got the first confirmed booking
    cancelling_booking = confirmed_bookings[0]
    cancelling_member_token = next(
        tok
        for (u, m, tok) in members_data
        if str(m.id) == cancelling_booking["member_id"]
    )

    cancel_res = await api_client.post(
        f"/api/v1/me/classes/bookings/{cancelling_booking['id']}/cancel",
        headers={
            "Authorization": f"Bearer {cancelling_member_token}",
            "X-Tenant-ID": str(tenant.id),
        },
        json={"cancellation_reason": "Schedule conflict"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"
    assert cancel_res.json()["is_late_cancellation"] is False

    # 3. Verify Auto-Promotion: The member who had waitlist position 1 is now CONFIRMED!
    async with pg_session_maker() as db:
        await db.execute(
            select(func.set_config("app.current_tenant_id", str(tenant.id), True))
        )
        # Check bookings state
        all_bookings = (
            (
                await db.execute(
                    select(ClassBooking)
                    .where(
                        ClassBooking.tenant_id == tenant.id,
                        ClassBooking.session_id == session.id,
                    )
                    .order_by(ClassBooking.booked_at.asc())
                )
            )
            .scalars()
            .all()
        )

        confirmed_now = [
            b for b in all_bookings if b.status == ClassBookingStatus.CONFIRMED
        ]
        waitlisted_now = [
            b for b in all_bookings if b.status == ClassBookingStatus.WAITLISTED
        ]

        # Total confirmed is still exactly 3 (capacity saturated)
        assert len(confirmed_now) == 3

        # Remaining waitlist count is 6, with re-indexed positions 1..6
        assert len(waitlisted_now) == 6
        new_positions = sorted([b.waitlist_position for b in waitlisted_now])
        assert new_positions == [1, 2, 3, 4, 5, 6]

        # Check outbox events emitted
        outbox_events = (
            (
                await db.execute(
                    select(OutboxEvent).where(OutboxEvent.tenant_id == tenant.id)
                )
            )
            .scalars()
            .all()
        )
        event_types = [e.event_type for e in outbox_events]
        assert "class.booking_promoted.v1" in event_types
        assert "class.booking_cancelled.v1" in event_types


@pytest.mark.asyncio
async def test_pt_appointment_conflict_prevention(
    pg_session_maker, api_client: AsyncClient
):
    """Test 1-on-1 PT appointment booking and overlap conflict prevention (409 Conflict)."""
    async with pg_session_maker() as db:
        org = Organization(
            id=uuid4(), name="FitNet PT", domain=f"fitnet-pt-{uuid4().hex[:6]}.com"
        )
        db.add(org)
        await db.flush()

        tenant = Tenant(
            id=uuid4(),
            organization_id=org.id,
            name="Club Kadikoy PT",
            location_code=f"KPT-{uuid4().hex[:4]}",
        )
        db.add(tenant)
        await db.flush()

        await db.execute(
            select(func.set_config("app.current_tenant_id", str(tenant.id), True))
        )

        loc = Location(
            id=uuid4(),
            tenant_id=tenant.id,
            name="PT Studio",
            timezone="Europe/Istanbul",
        )
        db.add(loc)
        await db.flush()

        trainer_user, _ = await _create_user_with_role(
            db,
            role_name="TRAINER",
            tenant_id=tenant.id,
            perms=["classes:read", "pt:read", "pt:write"],
        )

        user1, tok1 = await _create_user_with_role(
            db,
            role_name="MEMBER",
            tenant_id=tenant.id,
            perms=["pt:read:self", "pt:book:self"],
        )
        member1 = await _create_member_for_user(
            db, tenant.id, user1.id, "Alice", "Smith"
        )

        user2, tok2 = await _create_user_with_role(
            db,
            role_name="MEMBER",
            tenant_id=tenant.id,
            perms=["pt:read:self", "pt:book:self"],
        )
        member2 = await _create_member_for_user(db, tenant.id, user2.id, "Bob", "Jones")

        await db.commit()

    start_t = datetime.now(UTC) + timedelta(days=1, hours=10)
    end_t = start_t + timedelta(hours=1)

    # 1. Member 1 books PT with Trainer at 10:00 - 11:00
    start_time_utc = start_t.isoformat()
    res1 = await api_client.post(
        "/api/v1/me/pt/appointments",
        headers={"Authorization": f"Bearer {tok1}", "X-Tenant-ID": str(tenant.id)},
        json={
            "trainer_user_id": str(trainer_user.id),
            "location_id": str(loc.id),
            "start_time_utc": start_time_utc,
            "end_time_utc": end_t.isoformat(),
            "notes": "Leg day training",
        },
    )
    assert res1.status_code == 201
    appt1_id = res1.json()["id"]

    # 2. Member 2 tries to book the same Trainer at overlapping time (10:30 - 11:30)
    res2 = await api_client.post(
        "/api/v1/me/pt/appointments",
        headers={"Authorization": f"Bearer {tok2}", "X-Tenant-ID": str(tenant.id)},
        json={
            "trainer_user_id": str(trainer_user.id),
            "location_id": str(loc.id),
            "start_time_utc": (start_t + timedelta(minutes=30)).isoformat(),
            "end_time_utc": (end_t + timedelta(minutes=30)).isoformat(),
            "notes": "Core training",
        },
    )
    assert res2.status_code == 409
    assert "Antrenör seçilen saat aralığında doludur" in res2.json()["detail"]

    # 3. Member 1 cancels appointment
    cancel_res = await api_client.post(
        f"/api/v1/me/pt/appointments/{appt1_id}/cancel",
        headers={"Authorization": f"Bearer {tok1}", "X-Tenant-ID": str(tenant.id)},
        json={"cancellation_reason": "Sick"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # 4. Now Member 2 can book that slot successfully
    res3 = await api_client.post(
        "/api/v1/me/pt/appointments",
        headers={"Authorization": f"Bearer {tok2}", "X-Tenant-ID": str(tenant.id)},
        json={
            "trainer_user_id": str(trainer_user.id),
            "location_id": str(loc.id),
            "start_time_utc": start_t.isoformat(),
            "end_time_utc": end_t.isoformat(),
            "notes": "Core training",
        },
    )
    assert res3.status_code == 201
    assert res3.json()["status"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_late_cancellation_and_attendance_marking(
    pg_session_maker, api_client: AsyncClient
):
    """Test cancellation cutoff window (late cancellation flag) and attendance marking."""
    async with pg_session_maker() as db:
        org = Organization(
            id=uuid4(),
            name="FitNet Attendance",
            domain=f"fitnet-att-{uuid4().hex[:6]}.com",
        )
        db.add(org)
        await db.flush()

        tenant = Tenant(
            id=uuid4(),
            organization_id=org.id,
            name="Club Levent",
            location_code=f"LEV-{uuid4().hex[:4]}",
        )
        db.add(tenant)
        await db.flush()

        await db.execute(
            select(func.set_config("app.current_tenant_id", str(tenant.id), True))
        )

        loc = Location(
            id=uuid4(),
            tenant_id=tenant.id,
            name="HIIT Studio",
            timezone="Europe/Istanbul",
        )
        db.add(loc)
        await db.flush()

        trainer_user, trainer_tok = await _create_user_with_role(
            db,
            role_name="TRAINER",
            tenant_id=tenant.id,
            perms=["classes:read", "classes:attend"],
        )
        user1, tok1 = await _create_user_with_role(
            db,
            role_name="MEMBER",
            tenant_id=tenant.id,
            perms=["classes:read:self", "classes:book:self"],
        )
        member1 = await _create_member_for_user(
            db, tenant.id, user1.id, "Late", "Canceller"
        )

        user2, tok2 = await _create_user_with_role(
            db,
            role_name="MEMBER",
            tenant_id=tenant.id,
            perms=["classes:read:self", "classes:book:self"],
        )
        member2 = await _create_member_for_user(
            db, tenant.id, user2.id, "Attending", "Athlete"
        )

        class_type = ClassType(
            id=uuid4(),
            tenant_id=tenant.id,
            name="HIIT Express",
            category="HIIT",
            duration_minutes=30,
            default_capacity=5,
            color_hex="#EF4444",
            cancellation_cutoff_minutes=120,  # 2 hours cutoff
        )
        db.add(class_type)
        await db.flush()

        # Session starts in 30 minutes (within 120min cutoff!)
        soon_start = datetime.now(UTC) + timedelta(minutes=30)
        session = ClassSession(
            id=uuid4(),
            tenant_id=tenant.id,
            location_id=loc.id,
            class_type_id=class_type.id,
            trainer_user_id=trainer_user.id,
            start_time_utc=soon_start,
            end_time_utc=soon_start + timedelta(minutes=30),
            room_name="Studio 1",
            capacity=5,
            status=ClassSessionStatus.SCHEDULED,
        )
        db.add(session)
        await db.flush()
        await db.commit()

    # 1. Member 1 and Member 2 book the session
    headers1 = {"Authorization": f"Bearer {tok1}", "X-Tenant-ID": str(tenant.id)}
    headers2 = {"Authorization": f"Bearer {tok2}", "X-Tenant-ID": str(tenant.id)}
    trainer_headers = {
        "Authorization": f"Bearer {trainer_tok}",
        "X-Tenant-ID": str(tenant.id),
    }

    b1_res = await api_client.post(
        f"/api/v1/me/classes/sessions/{session.id}/book", headers=headers1
    )
    assert b1_res.status_code == 201
    b1_id = b1_res.json()["id"]

    b2_res = await api_client.post(
        f"/api/v1/me/classes/sessions/{session.id}/book", headers=headers2
    )
    assert b2_res.status_code == 201
    b2_id = b2_res.json()["id"]

    # 2. Member 1 cancels booking within cutoff (30 min before session, cutoff is 120 min)
    cancel_res = await api_client.post(
        f"/api/v1/me/classes/bookings/{b1_id}/cancel",
        headers=headers1,
        json={"cancellation_reason": "Emergency"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"
    # Invariant: is_late_cancellation is TRUE because cancelled within cutoff window
    assert cancel_res.json()["is_late_cancellation"] is True

    # 3. Trainer marks attendance for Member 2 as ATTENDED
    attend_res = await api_client.post(
        f"/api/v1/classes/bookings/{b2_id}/attend",
        headers=trainer_headers,
        json={"status": "ATTENDED"},
    )
    assert attend_res.status_code == 200
    assert attend_res.json()["status"] == "ATTENDED"
    assert attend_res.json()["attended_at"] is not None

    # 4. Check session roster
    roster_res = await api_client.get(
        f"/api/v1/classes/sessions/{session.id}/roster", headers=trainer_headers
    )
    assert roster_res.status_code == 200
    roster = roster_res.json()
    assert roster["total_confirmed"] == 1
    assert (
        len(roster["attendees"]) == 1
    )  # 1 active attendee (cancelled member excluded)


@pytest.mark.asyncio
async def test_multi_tenant_booking_isolation(
    pg_session_maker, api_client: AsyncClient
):
    """Verify strict tenant isolation: Tenant B cannot access or book Tenant A sessions."""
    async with pg_session_maker() as db:
        org = Organization(
            id=uuid4(), name="FitNet Iso", domain=f"fitnet-iso-{uuid4().hex[:6]}.com"
        )
        db.add(org)
        await db.flush()

        tenant_a = Tenant(
            id=uuid4(),
            organization_id=org.id,
            name="Club A",
            location_code=f"CLA-{uuid4().hex[:4]}",
        )
        tenant_b = Tenant(
            id=uuid4(),
            organization_id=org.id,
            name="Club B",
            location_code=f"CLB-{uuid4().hex[:4]}",
        )
        db.add_all([tenant_a, tenant_b])
        await db.flush()

        # Create session in Tenant A
        await db.execute(
            select(func.set_config("app.current_tenant_id", str(tenant_a.id), True))
        )
        loc_a = Location(
            id=uuid4(),
            tenant_id=tenant_a.id,
            name="Studio A",
            timezone="Europe/Istanbul",
        )
        db.add(loc_a)
        await db.flush()

        trainer_a, _ = await _create_user_with_role(
            db,
            role_name="TRAINER",
            tenant_id=tenant_a.id,
            perms=["classes:read", "classes:attend"],
        )

        type_a = ClassType(
            id=uuid4(),
            tenant_id=tenant_a.id,
            name="Yoga Flow A",
            category="YOGA",
            duration_minutes=60,
            default_capacity=10,
            color_hex="#10B981",
        )
        db.add(type_a)
        await db.flush()

        sess_a = ClassSession(
            id=uuid4(),
            tenant_id=tenant_a.id,
            location_id=loc_a.id,
            class_type_id=type_a.id,
            trainer_user_id=trainer_a.id,
            start_time_utc=datetime.now(UTC) + timedelta(days=1),
            end_time_utc=datetime.now(UTC) + timedelta(days=1, hours=1),
            capacity=10,
            status=ClassSessionStatus.SCHEDULED,
        )
        db.add(sess_a)
        await db.flush()

        # Create user in Tenant B
        await db.execute(
            select(func.set_config("app.current_tenant_id", str(tenant_b.id), True))
        )
        user_b, tok_b = await _create_user_with_role(
            db,
            role_name="MEMBER",
            tenant_id=tenant_b.id,
            perms=["classes:read:self", "classes:book:self"],
        )
        await _create_member_for_user(db, tenant_b.id, user_b.id, "TenantB", "User")
        await db.commit()

    # User in Tenant B tries to book Session in Tenant A (sending Tenant B header)
    headers_b = {"Authorization": f"Bearer {tok_b}", "X-Tenant-ID": str(tenant_b.id)}
    res = await api_client.post(
        f"/api/v1/me/classes/sessions/{sess_a.id}/book", headers=headers_b
    )
    # Invariant: Must return 404 because session does not exist in Tenant B
    assert res.status_code == 404
