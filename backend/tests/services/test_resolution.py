from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.member import Member
from app.models.membership import (
    Membership,
    MembershipPeriod,
    MembershipRenewal,
    Plan,
    PlanVersion,
)
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.services.resolution import ResolutionEngine

@pytest.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.fixture
async def setup_tenant(db_session):
    org = Organization(name="Test Org", domain=f"test-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t_id = uuid4()
    tenant = Tenant(
        id=t_id, 
        name="Test Tenant", 
        organization_id=org.id,
        location_code=f"LOC-{t_id}"
    )
    db_session.add(tenant)
    await db_session.commit()
    return tenant

@pytest.fixture
async def setup_base_data(db_session, setup_tenant):
    tenant_id = setup_tenant.id
    
    # Create member
    member = Member(
        id=uuid4(),
        tenant_id=tenant_id,
        member_number=f"MEM-{uuid4().hex[:6]}",
        first_name="Test",
        last_name="Member",
        email=f"test-{uuid4()}@example.com",
    )
    db_session.add(member)
    
    # Create Plan
    plan = Plan(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Test Plan"
    )
    db_session.add(plan)
    
    # Create PlanVersion
    pv = PlanVersion(
        id=uuid4(),
        tenant_id=tenant_id,
        plan_id=plan.id,
        version=1,
        price_amount_minor=1000,
        currency="TRY",
        billing_cycle_months=1,
        terms={},
        is_published=True,
        published_at=datetime.now(UTC)
    )
    db_session.add(pv)
    await db_session.commit()
    
    return member, plan, pv

@pytest.mark.asyncio
async def test_activate_scheduled_memberships(db_session, setup_tenant, setup_base_data):
    tenant_id = setup_tenant.id
    member, plan, pv = setup_base_data
    now = datetime.now(UTC)
    
    start_date = now - timedelta(days=1)
    end_date = start_date + relativedelta(months=1)
    
    m = Membership(
        id=uuid4(),
        tenant_id=tenant_id,
        member_id=member.id,
        plan_version_id=pv.id,
        status="SCHEDULED",
        start_date=start_date,
        end_date=end_date,
        price_snapshot=1000,
        price_snapshot_currency="TRY",
        terms_snapshot={}
    )
    db_session.add(m)
    
    p = MembershipPeriod(
        membership_id=m.id,
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        is_active=False
    )
    db_session.add(p)
    await db_session.commit()

    engine = ResolutionEngine(db_session)
    await engine.activate_scheduled_memberships()
    
    await db_session.refresh(m)
    assert m.status == "ACTIVE"
    await db_session.refresh(p)
    assert p.is_active == True

@pytest.mark.asyncio
async def test_process_expirations(db_session, setup_tenant, setup_base_data):
    tenant_id = setup_tenant.id
    member, plan, pv = setup_base_data
    now = datetime.now(UTC)
    
    m = Membership(
        id=uuid4(),
        tenant_id=tenant_id,
        member_id=member.id,
        plan_version_id=pv.id,
        status="ACTIVE",
        start_date=now - timedelta(days=30),
        end_date=now - timedelta(days=1),
        price_snapshot=1000,
        price_snapshot_currency="TRY",
        terms_snapshot={}
    )
    db_session.add(m)
    await db_session.commit()

    engine = ResolutionEngine(db_session)
    await engine.process_expirations()
    
    await db_session.refresh(m)
    assert m.status == "EXPIRED"

@pytest.mark.asyncio
async def test_process_renewals(db_session, setup_tenant, setup_base_data):
    tenant_id = setup_tenant.id
    member, plan, pv = setup_base_data
    now = datetime.now(UTC)
    
    next_pv = PlanVersion(
        id=uuid4(),
        tenant_id=tenant_id,
        plan_id=plan.id,
        version=2,
        price_amount_minor=1200,
        currency="TRY",
        billing_cycle_months=1,
        terms={},
        is_published=True,
        published_at=now
    )
    db_session.add(next_pv)
    await db_session.flush()
    
    m = Membership(
        id=uuid4(),
        tenant_id=tenant_id,
        member_id=member.id,
        plan_version_id=pv.id,
        status="ACTIVE",
        start_date=now - timedelta(days=60),
        end_date=now + timedelta(days=5),
        price_snapshot=1000,
        price_snapshot_currency="TRY",
        terms_snapshot={}
    )
    db_session.add(m)
    
    p = MembershipPeriod(
        membership_id=m.id,
        tenant_id=tenant_id,
        start_date=now - timedelta(days=25),
        end_date=now + timedelta(days=5),
        is_active=True
    )
    db_session.add(p)
    
    r = MembershipRenewal(
        id=uuid4(),
        tenant_id=tenant_id,
        membership_id=m.id,
        next_plan_version_id=next_pv.id,
        renewal_date=now - timedelta(hours=1),
        status="PENDING",
        price_snapshot=1200,
        price_snapshot_currency="TRY",
        terms_snapshot={}
    )
    db_session.add(r)
    await db_session.commit()

    engine = ResolutionEngine(db_session)
    await engine.process_renewals()
    
    await db_session.refresh(m)
    await db_session.refresh(r)
    await db_session.refresh(p)
    
    assert m.plan_version_id == next_pv.id
    assert r.status == "PROCESSED"
    assert p.is_active == False
