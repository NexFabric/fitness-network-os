from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.member import Member
from app.models.membership import (
    Membership,
    MembershipPeriod,
    MembershipRenewal,
    Plan,
    PlanVersion,
    RenewalStatus,
)
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.services.resolution import ResolutionEngine


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture
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

@pytest_asyncio.fixture
async def setup_tenant_2(db_session):
    org = Organization(name="Test Org 2", domain=f"test-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t_id = uuid4()
    tenant = Tenant(
        id=t_id, 
        name="Test Tenant 2", 
        organization_id=org.id,
        location_code=f"LOC-{t_id}"
    )
    db_session.add(tenant)
    await db_session.commit()
    return tenant

@pytest_asyncio.fixture
async def setup_base_data(db_session, setup_tenant):
    tenant_id = setup_tenant.id
    
    member = Member(
        id=uuid4(),
        tenant_id=tenant_id,
        member_number=f"MEM-{uuid4().hex[:6]}",
        first_name="Test",
        last_name="Member",
        email=f"test-{uuid4()}@example.com",
    )
    db_session.add(member)
    
    plan = Plan(
        id=uuid4(),
        tenant_id=tenant_id,
        name="Test Plan"
    )
    db_session.add(plan)
    
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
async def test_activate_scheduled_memberships(db_session, pg_session_maker, setup_tenant, setup_base_data):
    tenant_id = setup_tenant.id
    member, _plan, pv = setup_base_data
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

    async with pg_session_maker() as runtime_session:
        engine = ResolutionEngine(runtime_session)
        await engine.run_for_tenant(tenant_id)
        await runtime_session.commit()
    
    await db_session.refresh(m)
    assert m.status == "ACTIVE"
    await db_session.refresh(p)
    assert p.is_active

@pytest.mark.asyncio
async def test_process_expirations(db_session, pg_session_maker, setup_tenant, setup_base_data):
    tenant_id = setup_tenant.id
    member, _plan, pv = setup_base_data
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

    p = MembershipPeriod(
        membership_id=m.id,
        tenant_id=tenant_id,
        start_date=now - timedelta(days=30),
        end_date=now - timedelta(days=1),
        is_active=True
    )
    db_session.add(p)
    await db_session.commit()

    async with pg_session_maker() as runtime_session:
        engine = ResolutionEngine(runtime_session)
        await engine.run_for_tenant(tenant_id)
        await runtime_session.commit()
    
    await db_session.refresh(m)
    assert m.status == "EXPIRED"
    await db_session.refresh(p)
    assert not p.is_active

@pytest.mark.asyncio
async def test_process_renewals(db_session, pg_session_maker, setup_tenant, setup_base_data):
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
        status=RenewalStatus.PENDING.value,
        price_snapshot=1200,
        price_snapshot_currency="TRY",
        terms_snapshot={}
    )
    db_session.add(r)
    await db_session.commit()

    async with pg_session_maker() as runtime_session:
        engine = ResolutionEngine(runtime_session)
        await engine.run_for_tenant(tenant_id)
        await runtime_session.commit()
    
    await db_session.refresh(m)
    await db_session.refresh(r)
    await db_session.refresh(p)
    
    assert m.plan_version_id == next_pv.id
    assert r.status == RenewalStatus.APPLIED.value
    assert not p.is_active
    
    stmt = select(MembershipPeriod).where(MembershipPeriod.membership_id == m.id, MembershipPeriod.is_active)
    active_period = (await db_session.execute(stmt)).scalar_one_or_none()
    assert active_period is not None
    assert active_period.start_date == p.end_date

@pytest.mark.asyncio
async def test_two_tenant_isolation(db_session, pg_session_maker, setup_tenant, setup_tenant_2, setup_base_data):
    """Prove the worker only sees the target tenant's data."""
    t1_id = setup_tenant.id
    t2_id = setup_tenant_2.id
    
    member, _plan, pv = setup_base_data
    now = datetime.now(UTC)
    start_date = now - timedelta(days=1)
    end_date = start_date + relativedelta(months=1)
    
    # Scheduled for tenant 1
    m1 = Membership(
        id=uuid4(),
        tenant_id=t1_id,
        member_id=member.id,
        plan_version_id=pv.id,
        status="SCHEDULED",
        start_date=start_date,
        end_date=end_date,
        price_snapshot=1000,
        price_snapshot_currency="TRY",
        terms_snapshot={}
    )
    p1 = MembershipPeriod(membership_id=m1.id, tenant_id=t1_id, start_date=start_date, end_date=end_date, is_active=False)
    
    # Create member, plan, and pv for tenant 2
    member2 = Member(
        id=uuid4(),
        tenant_id=t2_id,
        member_number=f"MEM-{uuid4().hex[:6]}",
        first_name="Test2",
        last_name="Member2",
        email=f"test2-{uuid4()}@example.com",
    )
    db_session.add(member2)
    
    plan2 = Plan(id=uuid4(), tenant_id=t2_id, name="Tenant 2 Plan")
    db_session.add(plan2)
    
    pv2 = PlanVersion(
        id=uuid4(),
        tenant_id=t2_id,
        plan_id=plan2.id,
        version=1,
        price_amount_minor=1000,
        currency="TRY",
        billing_cycle_months=1,
        terms={},
        is_published=True,
        published_at=now
    )
    db_session.add(pv2)
    await db_session.flush()

    # Scheduled for tenant 2
    m2 = Membership(
        id=uuid4(),
        tenant_id=t2_id,
        member_id=member2.id,
        plan_version_id=pv2.id,
        status="SCHEDULED",
        start_date=start_date,
        end_date=end_date,
        price_snapshot=1000,
        price_snapshot_currency="TRY",
        terms_snapshot={}
    )
    p2 = MembershipPeriod(membership_id=m2.id, tenant_id=t2_id, start_date=start_date, end_date=end_date, is_active=False)
    
    db_session.add_all([m1, p1, m2, p2])
    await db_session.commit()

    async with pg_session_maker() as runtime_session:
        engine = ResolutionEngine(runtime_session)
        # Process ONLY for tenant 2
        await engine.run_for_tenant(t2_id)
        await runtime_session.commit()
    
    await db_session.refresh(m1)
    await db_session.refresh(m2)
    
    # m1 remains SCHEDULED because it belongs to t1
    assert m1.status == "SCHEDULED"
    # m2 becomes ACTIVE because we ran engine for t2
    assert m2.status == "ACTIVE"

@pytest.mark.asyncio
async def test_renewal_error_isolation(setup_base_data, pg_session_maker, setup_tenant, db_session):
    tenant_id = setup_tenant.id
    member, _plan, pv = setup_base_data
    now = datetime.now(UTC)

    m1 = Membership(
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
    p1 = MembershipPeriod(membership_id=m1.id, tenant_id=tenant_id, start_date=m1.start_date, end_date=m1.end_date, is_active=True)
    r1 = MembershipRenewal(
        id=uuid4(),
        tenant_id=tenant_id,
        membership_id=m1.id,
        next_plan_version_id=pv.id,
        renewal_date=now - timedelta(hours=2),
        status=RenewalStatus.PENDING.value,
        price_snapshot=1000,
        price_snapshot_currency="TRY",
        terms_snapshot={}
    )
    
    m2 = Membership(
        id=uuid4(),
        tenant_id=tenant_id,
        member_id=member.id,
        plan_version_id=pv.id,
        status="ACTIVE",
        start_date=now - timedelta(days=30),
        end_date=now + timedelta(days=5),
        price_snapshot=1000,
        price_snapshot_currency="TRY",
        terms_snapshot={}
    )
    p2 = MembershipPeriod(membership_id=m2.id, tenant_id=tenant_id, start_date=m2.start_date, end_date=m2.end_date, is_active=True)
    r2 = MembershipRenewal(
        id=uuid4(),
        tenant_id=tenant_id,
        membership_id=m2.id,
        next_plan_version_id=pv.id,
        renewal_date=now - timedelta(hours=1),
        status=RenewalStatus.PENDING.value,
        price_snapshot=1000,
        price_snapshot_currency="TRY",
        terms_snapshot={}
    )
    
    db_session.add_all([m1, p1, r1, m2, p2, r2])
    await db_session.commit()

    async with pg_session_maker() as runtime_session:
        engine = ResolutionEngine(runtime_session)
        original_get = engine.membership_service.get_membership
        
        async def mock_get(mid, *args, **kwargs):
            if mid == m1.id:
                raise ValueError("Simulated failure")
            return await original_get(mid, *args, **kwargs)
            
        engine.membership_service.get_membership = mock_get
        await engine.run_for_tenant(tenant_id)
        await runtime_session.commit()
    
    await db_session.refresh(r1)
    await db_session.refresh(r2)
        
    assert r1.status == RenewalStatus.FAILED.value
    assert r2.status == RenewalStatus.APPLIED.value
