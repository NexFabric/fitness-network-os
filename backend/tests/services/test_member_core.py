"""Phase 14 member / gym core — real PostgreSQL tests."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.organization import Organization
from app.models.tenant import Tenant
from app.models.user import User
from app.services.location import LocationService
from app.services.member import MemberService
from app.services.staff import StaffService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Core Org", domain=f"core-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="Core Tenant",
        organization_id=org.id,
        location_code=f"C-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


@pytest.mark.asyncio
async def test_create_and_status_transition(db_session, tenant):
    svc = MemberService(db_session)
    m = await svc.create_member(
        tenant.id,
        member_number="M-100",
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
    )
    await db_session.commit()
    assert m.status == "LEAD"

    m = await svc.set_status(tenant.id, m.id, "ACTIVE")
    await db_session.commit()
    assert m.status == "ACTIVE"

    with pytest.raises(ValueError, match="invalid_transition"):
        await svc.set_status(tenant.id, m.id, "LEAD")


@pytest.mark.asyncio
async def test_member_number_unique_per_tenant(db_session, tenant):
    svc = MemberService(db_session)
    await svc.create_member(
        tenant.id, member_number="DUP-1", first_name="A", last_name="B"
    )
    await db_session.commit()

    with pytest.raises(ValueError, match="member_number_conflict"):
        await svc.create_member(
            tenant.id, member_number="DUP-1", first_name="C", last_name="D"
        )
        await db_session.flush()


@pytest.mark.asyncio
async def test_tags_notes_consent(db_session, tenant):
    svc = MemberService(db_session)
    m = await svc.create_member(
        tenant.id, member_number="M-200", first_name="Grace", last_name="Hopper"
    )
    await db_session.commit()

    tag = await svc.add_tag(tenant.id, m.id, "VIP")
    note = await svc.add_note(tenant.id, m.id, "Prefers morning classes")
    await svc.ensure_consent_definition(
        tenant.id, name="Marketing", consent_type="MARKETING"
    )
    consent = await svc.record_consent(
        tenant.id,
        m.id,
        consent_type="MARKETING",
        document_version="v1",
        status="GIVEN",
    )
    await db_session.commit()

    tags = await svc.list_tags(tenant.id, m.id)
    notes = await svc.list_notes(tenant.id, m.id)
    assert tag.name == "VIP"
    assert any(t.name == "VIP" for t in tags)
    assert notes[0].content.startswith("Prefers")
    assert consent.status == "GIVEN"


@pytest.mark.asyncio
async def test_location_crud(db_session, tenant):
    svc = LocationService(db_session)
    loc = await svc.create_location(
        tenant.id, name="Kadıköy", timezone="Europe/Istanbul", address="Moda"
    )
    await db_session.commit()
    locs = await svc.list_locations(tenant.id)
    assert len(locs) == 1
    updated = await svc.update_location(tenant.id, loc.id, name="Kadikoy Branch")
    await db_session.commit()
    assert updated.name == "Kadikoy Branch"


@pytest.mark.asyncio
async def test_staff_link(db_session, tenant):
    user = User(
        id=uuid4(),
        email=f"staff-{uuid4()}@example.com",
        hashed_password="hashed-not-used",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    loc_svc = LocationService(db_session)
    loc = await loc_svc.create_location(tenant.id, name="HQ")
    await db_session.commit()

    staff_svc = StaffService(db_session)
    staff = await staff_svc.link_staff(
        tenant.id, user_id=user.id, role="TRAINER", location_id=loc.id
    )
    await db_session.commit()
    assert staff.role == "TRAINER"
    assert staff.location_id == loc.id

    # Idempotent relink updates role
    staff2 = await staff_svc.link_staff(
        tenant.id, user_id=user.id, role="MANAGER", location_id=loc.id
    )
    await db_session.commit()
    assert staff2.id == staff.id
    assert staff2.role == "MANAGER"

    listed = await staff_svc.list_staff(tenant.id)
    assert len(listed) == 1
