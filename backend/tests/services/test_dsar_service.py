"""DSAR service branches beyond the HTTP export/erasure specs."""

import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
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
    PtAppointment,
    PtAppointmentStatus,
)
from app.models.consent import ConsentRecord
from app.models.dsar import (
    KIND_ERASURE,
    STATUS_COMPLETED,
    STATUS_PACKAGED,
    STATUS_RECEIVED,
    STATUS_REJECTED,
    DsarRequest,
)
from app.models.location import Location
from app.models.member import Member, Note
from app.models.membership import Membership, Plan, PlanVersion
from app.models.organization import Organization
from app.models.staff import Staff
from app.models.tenant import Tenant
from app.models.user import User, UserSession
from app.services.booking import BookingConflict, BookingNotFound
from app.services.dsar import (
    HOLD_OPEN_INVOICES,
    DsarService,
    _assert_package_safe,
    _iso,
)


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest.mark.asyncio
async def test_dsar_list_and_get(db_session: AsyncSession):
    org = Organization(name="Dsar Org", domain=f"ds-{uuid4().hex[:8]}.com")
    db_session.add(org)
    await db_session.flush()
    tenant = Tenant(
        id=uuid4(),
        name="Dsar T",
        organization_id=org.id,
        location_code=f"DS-{uuid4().hex[:6]}",
    )
    db_session.add(tenant)
    await db_session.flush()
    member = Member(
        id=uuid4(),
        tenant_id=tenant.id,
        member_number=f"M-{uuid4().hex[:6]}",
        first_name="Ada",
        last_name="Lovelace",
        email=f"ada-{uuid4().hex[:6]}@example.com",
    )
    db_session.add(member)
    await db_session.commit()

    svc = DsarService(db_session)
    row, created = await svc.request_export(
        tenant.id, member, requested_by_user_id=None
    )
    await db_session.commit()
    assert created is True
    again, created_again = await svc.request_export(
        tenant.id, member, requested_by_user_id=None
    )
    assert created_again is False
    assert again.id == row.id

    listed = await svc.list_for_member(tenant.id, member.id)
    assert [item.id for item in listed] == [row.id]
    tenant_list = await svc.list_for_tenant(tenant.id)
    assert [item.id for item in tenant_list] == [row.id]
    fetched = await svc.get(tenant.id, row.id)
    assert fetched is not None
    assert fetched.id == row.id
    assert await svc.get(tenant.id, uuid4()) is None


def test_dsar_package_rejects_secret_keys():
    with pytest.raises(ValueError, match="package_contains_secret:hashed_password"):
        _assert_package_safe({"profile": {"hashed_password": "x"}})
    _assert_package_safe({"email": "a@b.c", "invoices": [{"amount_minor": 100}]})


def test_iso_none_and_naive_datetime():
    assert _iso(None) is None
    naive = datetime(2026, 1, 2, 3, 4, 5)  # noqa: DTZ001 — _iso naive branch
    assert _iso(naive) == "2026-01-02T03:04:05+00:00"
    aware = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    assert _iso(aware) == "2026-01-02T03:04:05+00:00"


async def _member_world(db: AsyncSession):
    org = Organization(name="Erase Org", domain=f"er-{uuid4().hex[:8]}.com")
    db.add(org)
    await db.flush()
    tenant = Tenant(
        id=uuid4(),
        name="Erase T",
        organization_id=org.id,
        location_code=f"ER-{uuid4().hex[:6]}",
    )
    db.add(tenant)
    await db.flush()
    user = User(
        email=f"erase-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=f"th_{uuid4().hex}",
            expires_at=datetime.now(UTC) + timedelta(days=1),
            is_revoked=False,
        )
    )
    member = Member(
        id=uuid4(),
        tenant_id=tenant.id,
        member_number=f"E-{uuid4().hex[:6]}",
        first_name="Silinecek",
        last_name="Kisi",
        email="erase-me@example.com",
        phone="+905551112233",
        status="ACTIVE",
        user_id=user.id,
    )
    db.add(member)
    await db.flush()
    return tenant, member, user


@pytest.mark.asyncio
async def test_download_url_requires_packaged_uri(db_session: AsyncSession):
    tenant, member, _user = await _member_world(db_session)
    svc = DsarService(db_session)
    row = DsarRequest(
        tenant_id=tenant.id,
        member_id=member.id,
        kind="EXPORT",
        status=STATUS_RECEIVED,
        due_at=datetime.now(UTC) + timedelta(days=30),
    )
    assert await svc.download_url(tenant.id, row) is None
    row.status = STATUS_PACKAGED
    row.package_uri = None
    assert await svc.download_url(tenant.id, row) is None


@pytest.mark.asyncio
async def test_request_erasure_anonymizes_related_rows_and_is_idempotent(
    db_session: AsyncSession,
):
    tenant, member, user = await _member_world(db_session)
    note = Note(tenant_id=tenant.id, member_id=member.id, content="private note")
    consent = ConsentRecord(
        tenant_id=tenant.id,
        member_id=member.id,
        consent_type="MARKETING",
        document_version="v1",
        status="GIVEN",
        given_at=datetime.now(UTC),
    )
    db_session.add_all([note, consent])
    plan = Plan(tenant_id=tenant.id, name="Basic")
    db_session.add(plan)
    await db_session.flush()
    version = PlanVersion(
        tenant_id=tenant.id,
        plan_id=plan.id,
        version=1,
        price_amount_minor=1000,
        billing_cycle_months=1,
    )
    db_session.add(version)
    await db_session.flush()
    membership = Membership(
        tenant_id=tenant.id,
        member_id=member.id,
        plan_version_id=version.id,
        status="ACTIVE",
        start_date=datetime.now(UTC) - timedelta(days=10),
    )
    db_session.add(membership)

    trainer = User(
        email=f"tr-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db_session.add(trainer)
    await db_session.flush()
    loc = Location(tenant_id=tenant.id, name="Studio", timezone="UTC")
    db_session.add(loc)
    await db_session.flush()
    db_session.add(Staff(tenant_id=tenant.id, user_id=trainer.id, role="TRAINER"))
    class_type = ClassType(
        tenant_id=tenant.id,
        name="HIIT",
        duration_minutes=45,
        default_capacity=8,
        cancellation_cutoff_minutes=30,
    )
    db_session.add(class_type)
    await db_session.flush()
    start = datetime.now(UTC) + timedelta(days=2)
    session = ClassSession(
        tenant_id=tenant.id,
        location_id=loc.id,
        class_type_id=class_type.id,
        trainer_user_id=trainer.id,
        start_time_utc=start,
        end_time_utc=start + timedelta(minutes=45),
        capacity=8,
        status=ClassSessionStatus.SCHEDULED,
    )
    db_session.add(session)
    await db_session.flush()
    booking = ClassBooking(
        tenant_id=tenant.id,
        session_id=session.id,
        member_id=member.id,
        status=ClassBookingStatus.CONFIRMED,
        booked_at=datetime.now(UTC),
    )
    db_session.add(booking)
    appt = PtAppointment(
        tenant_id=tenant.id,
        trainer_user_id=trainer.id,
        member_id=member.id,
        location_id=loc.id,
        start_time_utc=start,
        end_time_utc=start + timedelta(hours=1),
        status=PtAppointmentStatus.CONFIRMED,
        booked_at=datetime.now(UTC),
    )
    db_session.add(appt)
    await db_session.commit()

    svc = DsarService(db_session)
    row, created = await svc.request_erasure(
        tenant.id, member, requested_by_user_id=user.id
    )
    await db_session.commit()
    assert created is True
    assert row.status == STATUS_COMPLETED

    await db_session.refresh(member)
    await db_session.refresh(user)
    await db_session.refresh(membership)
    await db_session.refresh(booking)
    await db_session.refresh(appt)
    await db_session.refresh(note)
    await db_session.refresh(consent)
    sessions = list(
        (
            await db_session.execute(
                select(UserSession).where(UserSession.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    assert member.first_name == "ANON"
    assert member.last_name == member.member_number
    assert member.email is None
    assert member.phone is None
    assert member.status == "ANONYMIZED"
    assert member.user_id is None
    assert user.is_active is False
    assert all(s.is_revoked for s in sessions)
    assert note.content == "[anonymized]"
    assert consent.status == "WITHDRAWN"
    assert consent.withdrawn_at is not None
    assert membership.status == "CANCELLED"
    assert booking.status == ClassBookingStatus.CANCELLED
    assert appt.status == PtAppointmentStatus.CANCELLED

    again, created_again = await svc.request_erasure(
        tenant.id, member, requested_by_user_id=user.id
    )
    assert created_again is False
    assert again.id == row.id
    assert again.status == STATUS_COMPLETED


@pytest.mark.asyncio
async def test_request_erasure_retries_rejected_row(db_session: AsyncSession):
    tenant, member, user = await _member_world(db_session)
    existing = DsarRequest(
        tenant_id=tenant.id,
        member_id=member.id,
        requested_by_user_id=user.id,
        kind=KIND_ERASURE,
        status=STATUS_REJECTED,
        rejection_reason=HOLD_OPEN_INVOICES,
        due_at=datetime.now(UTC) + timedelta(days=5),
        dedupe_key=f"dsar-erasure:{member.id}",
    )
    db_session.add(existing)
    await db_session.commit()

    svc = DsarService(db_session)
    row, created = await svc.request_erasure(
        tenant.id, member, requested_by_user_id=user.id
    )
    await db_session.commit()
    assert created is True
    assert row.id == existing.id
    assert row.status == STATUS_COMPLETED
    assert row.rejection_reason is None


@pytest.mark.asyncio
async def test_request_erasure_swallows_booking_cancel_races(db_session: AsyncSession):
    tenant, member, user = await _member_world(db_session)
    trainer = User(
        email=f"tr-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db_session.add(trainer)
    await db_session.flush()
    loc = Location(tenant_id=tenant.id, name="Studio", timezone="UTC")
    db_session.add(loc)
    await db_session.flush()
    db_session.add(Staff(tenant_id=tenant.id, user_id=trainer.id, role="TRAINER"))
    class_type = ClassType(
        tenant_id=tenant.id,
        name="Spin",
        duration_minutes=40,
        default_capacity=6,
        cancellation_cutoff_minutes=15,
    )
    db_session.add(class_type)
    await db_session.flush()
    start = datetime.now(UTC) + timedelta(days=1)
    session = ClassSession(
        tenant_id=tenant.id,
        location_id=loc.id,
        class_type_id=class_type.id,
        trainer_user_id=trainer.id,
        start_time_utc=start,
        end_time_utc=start + timedelta(minutes=40),
        capacity=6,
        status=ClassSessionStatus.SCHEDULED,
    )
    db_session.add(session)
    await db_session.flush()
    db_session.add(
        ClassBooking(
            tenant_id=tenant.id,
            session_id=session.id,
            member_id=member.id,
            status=ClassBookingStatus.WAITLISTED,
            waitlist_position=1,
            booked_at=datetime.now(UTC),
        )
    )
    db_session.add(
        PtAppointment(
            tenant_id=tenant.id,
            trainer_user_id=trainer.id,
            member_id=member.id,
            location_id=loc.id,
            start_time_utc=start,
            end_time_utc=start + timedelta(hours=1),
            status=PtAppointmentStatus.CONFIRMED,
            booked_at=datetime.now(UTC),
        )
    )
    await db_session.commit()

    svc = DsarService(db_session)
    with (
        patch(
            "app.services.dsar.ClassBookingService.cancel_booking",
            new=AsyncMock(side_effect=BookingNotFound("gone")),
        ),
        patch(
            "app.services.dsar.PtBookingService.cancel_appointment",
            new=AsyncMock(side_effect=BookingConflict("busy")),
        ),
    ):
        row, created = await svc.request_erasure(
            tenant.id, member, requested_by_user_id=user.id
        )
    await db_session.commit()
    assert created is True
    assert row.status == STATUS_COMPLETED
    await db_session.refresh(member)
    assert member.status == "ANONYMIZED"


@pytest.mark.asyncio
async def test_export_package_includes_related_rows_and_download_url(
    db_session: AsyncSession,
):
    from app.models.access import AccessAttempt, AccessStatus, Checkin
    from app.models.finance import BillingAccount, Invoice, Payment

    tenant, member, user = await _member_world(db_session)
    loc = Location(tenant_id=tenant.id, name="Desk", timezone="UTC")
    db_session.add(loc)
    await db_session.flush()
    checkin = Checkin(
        tenant_id=tenant.id,
        member_id=member.id,
        location_id=loc.id,
        checkin_time=datetime.now(UTC) - timedelta(hours=2),
        checkout_time=datetime.now(UTC) - timedelta(hours=1),
    )
    attempt = AccessAttempt(
        tenant_id=tenant.id,
        member_id=member.id,
        status=AccessStatus.DENIED,
        denial_reason="expired_membership",
        timestamp=datetime.now(UTC),
    )
    account = BillingAccount(tenant_id=tenant.id, member_id=member.id)
    db_session.add_all([checkin, attempt, account])
    await db_session.flush()
    invoice = Invoice(
        tenant_id=tenant.id,
        billing_account_id=account.id,
        status="PAID",
        total_amount_minor=2500,
        paid_amount_minor=2500,
        discount_amount_minor=0,
        currency="TRY",
    )
    payment = Payment(
        tenant_id=tenant.id,
        billing_account_id=account.id,
        amount_minor=2500,
        refunded_amount_minor=0,
        currency="TRY",
        status="SUCCEEDED",
        method="CASH",
    )
    consent = ConsentRecord(
        tenant_id=tenant.id,
        member_id=member.id,
        consent_type="PRIVACY",
        document_version="v2",
        status="GIVEN",
        given_at=datetime.now(UTC),
    )
    plan = Plan(tenant_id=tenant.id, name="Pack")
    db_session.add(plan)
    await db_session.flush()
    version = PlanVersion(
        tenant_id=tenant.id,
        plan_id=plan.id,
        version=1,
        price_amount_minor=2500,
        billing_cycle_months=1,
    )
    db_session.add(version)
    await db_session.flush()
    membership = Membership(
        tenant_id=tenant.id,
        member_id=member.id,
        plan_version_id=version.id,
        status="ACTIVE",
        start_date=datetime.now(UTC) - timedelta(days=3),
    )
    trainer = User(
        email=f"tr-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db_session.add_all([invoice, payment, consent, membership, trainer])
    await db_session.flush()
    db_session.add(Staff(tenant_id=tenant.id, user_id=trainer.id, role="TRAINER"))
    class_type = ClassType(
        tenant_id=tenant.id,
        name="Export HIIT",
        duration_minutes=40,
        default_capacity=6,
        cancellation_cutoff_minutes=15,
    )
    db_session.add(class_type)
    await db_session.flush()
    start = datetime.now(UTC) + timedelta(days=2)
    session = ClassSession(
        tenant_id=tenant.id,
        location_id=loc.id,
        class_type_id=class_type.id,
        trainer_user_id=trainer.id,
        start_time_utc=start,
        end_time_utc=start + timedelta(minutes=40),
        capacity=6,
        status=ClassSessionStatus.SCHEDULED,
    )
    db_session.add(session)
    await db_session.flush()
    db_session.add(
        ClassBooking(
            tenant_id=tenant.id,
            session_id=session.id,
            member_id=member.id,
            status=ClassBookingStatus.CONFIRMED,
            booked_at=datetime.now(UTC),
        )
    )
    db_session.add(
        PtAppointment(
            tenant_id=tenant.id,
            trainer_user_id=trainer.id,
            member_id=member.id,
            location_id=loc.id,
            start_time_utc=start,
            end_time_utc=start + timedelta(hours=1),
            status=PtAppointmentStatus.CONFIRMED,
            booked_at=datetime.now(UTC),
        )
    )
    await db_session.commit()

    svc = DsarService(db_session)
    row, created = await svc.request_export(
        tenant.id, member, requested_by_user_id=user.id
    )
    await db_session.commit()
    assert created is True
    assert row.status == STATUS_PACKAGED
    url = await svc.download_url(tenant.id, row)
    assert url

    from pathlib import Path
    from urllib.parse import unquote, urlparse

    payload = json.loads(Path(unquote(urlparse(url).path)).read_text())
    assert payload["schema"] == "gymclubnex.dsar.export.v1"
    assert payload["member"]["email"] == "erase-me@example.com"
    assert payload["invoices"][0]["total_amount_minor"] == 2500
    assert payload["payments"][0]["amount_minor"] == 2500
    assert payload["checkins"][0]["checkout_time"] is not None
    assert payload["access_attempts"][0]["denial_reason"] == "expired_membership"
    assert payload["consents"][0]["consent_type"] == "PRIVACY"
    assert payload["memberships"][0]["status"] == "ACTIVE"
    assert "CONFIRMED" in str(payload["class_bookings"][0]["status"])
    assert "CONFIRMED" in str(payload["pt_appointments"][0]["status"])


@pytest.mark.asyncio
async def test_erasure_holds_draft_and_partial_invoices_and_unbound_member(
    db_session: AsyncSession,
):
    from app.models.finance import BillingAccount, Invoice
    from app.services.dsar import DsarLegalHold

    tenant, member, user = await _member_world(db_session)
    account = BillingAccount(tenant_id=tenant.id, member_id=member.id)
    db_session.add(account)
    await db_session.flush()
    draft = Invoice(
        tenant_id=tenant.id,
        billing_account_id=account.id,
        status="DRAFT",
        total_amount_minor=1000,
        paid_amount_minor=0,
        discount_amount_minor=0,
        currency="TRY",
    )
    db_session.add(draft)
    await db_session.commit()

    svc = DsarService(db_session)
    with pytest.raises(DsarLegalHold) as held:
        await svc.request_erasure(tenant.id, member, requested_by_user_id=user.id)
    assert held.value.reason == HOLD_OPEN_INVOICES
    assert held.value.row.status == STATUS_REJECTED

    draft.status = "PARTIALLY_PAID"
    draft.paid_amount_minor = 400
    await db_session.commit()
    with pytest.raises(DsarLegalHold):
        await svc.request_erasure(tenant.id, member, requested_by_user_id=user.id)

    draft.status = "PAID"
    draft.paid_amount_minor = 1000
    await db_session.commit()

    unbound = Member(
        tenant_id=tenant.id,
        member_number=f"U-{uuid4().hex[:6]}",
        first_name="Loose",
        last_name="Member",
        email="loose@example.com",
        phone="+905559990011",
        status="ACTIVE",
        user_id=None,
    )
    db_session.add(unbound)
    await db_session.commit()
    row, created = await svc.request_erasure(
        tenant.id, unbound, requested_by_user_id=None
    )
    await db_session.commit()
    assert created is True
    assert row.status == STATUS_COMPLETED
    await db_session.refresh(unbound)
    assert unbound.first_name == "ANON"
    assert unbound.email is None
    assert unbound.user_id is None


def test_dsar_package_rejects_card_secrets():
    for key in ("pan", "cvv", "card_number", "encrypted_secret"):
        with pytest.raises(ValueError, match=f"package_contains_secret:{key}"):
            _assert_package_safe({key: "x"})
