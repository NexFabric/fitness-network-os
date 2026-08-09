import pytest
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from dateutil.relativedelta import relativedelta

from app.models.membership import (
    Membership,
    MembershipRenewal,
    MembershipPeriod,
    PlanVersion,
)
from app.services.resolution import ResolutionEngine

@pytest.mark.asyncio
async def test_activate_scheduled_memberships(db_session, setup_tenant):
    # Setup
    tenant_id = setup_tenant.id
    now = datetime.now(UTC)
    member_id = uuid4()
    
    # Create PlanVersion
    pv = PlanVersion(
        id=uuid4(),
        tenant_id=tenant_id,
        plan_id=uuid4(),
        version=1,
        price_amount_minor=1000,
        currency="TRY",
        billing_cycle_months=1,
        terms={},
        is_published=True,
        published_at=now
    )
    db_session.add(pv)
    
    # Create scheduled membership
    start_date = now - timedelta(days=1)
    end_date = start_date + relativedelta(months=1)
    m = Membership(
        id=uuid4(),
        tenant_id=tenant_id,
        member_id=member_id,
        plan_version_id=pv.id,
        status="SCHEDULED",
        start_date=start_date,
        end_date=end_date,
        price_snapshot=1000,
        price_snapshot_currency="TRY",
        terms_snapshot={}
    )
    db_session.add(m)
    
    # Create period
    p = MembershipPeriod(
        membership_id=m.id,
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        is_active=False
    )
    db_session.add(p)
    
    await db_session.commit()

    # Run resolution
    engine = ResolutionEngine(db_session)
    await engine.activate_scheduled_memberships()
    
    # Verify
    await db_session.refresh(m)
    assert m.status == "ACTIVE"
    await db_session.refresh(p)
    assert p.is_active == True

@pytest.mark.asyncio
async def test_process_expirations(db_session, setup_tenant):
    tenant_id = setup_tenant.id
    now = datetime.now(UTC)
    member_id = uuid4()
    
    m = Membership(
        id=uuid4(),
        tenant_id=tenant_id,
        member_id=member_id,
        plan_version_id=uuid4(),
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
async def test_process_renewals(db_session, setup_tenant):
    tenant_id = setup_tenant.id
    now = datetime.now(UTC)
    member_id = uuid4()
    
    # Create next PlanVersion
    next_pv = PlanVersion(
        id=uuid4(),
        tenant_id=tenant_id,
        plan_id=uuid4(),
        version=2,
        price_amount_minor=1200,
        currency="TRY",
        billing_cycle_months=1,
        terms={},
        is_published=True,
        published_at=now
    )
    db_session.add(next_pv)
    
    m = Membership(
        id=uuid4(),
        tenant_id=tenant_id,
        member_id=member_id,
        plan_version_id=uuid4(),
        status="ACTIVE",
        start_date=now - timedelta(days=60),
        end_date=now + timedelta(days=5),
        price_snapshot=1000,
        price_snapshot_currency="TRY",
        terms_snapshot={}
    )
    db_session.add(m)
    
    # Create active period
    p = MembershipPeriod(
        membership_id=m.id,
        tenant_id=tenant_id,
        start_date=now - timedelta(days=25),
        end_date=now + timedelta(days=5),
        is_active=True
    )
    db_session.add(p)
    
    # Create pending renewal
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
