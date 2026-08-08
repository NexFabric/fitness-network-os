from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from app.models.membership import Membership, MembershipFreeze, Plan, PlanVersion, StatusHistory
from app.models.member import Member
from app.models.tenant import Tenant
from app.services.membership import MembershipService

from app.models.organization import Organization

@pytest.fixture
async def db_session(pg_session_maker) -> AsyncGenerator[AsyncSession, None]:
    async with pg_session_maker() as session:
        yield session

@pytest.fixture
async def tenant_id(db_session: AsyncSession) -> UUID:
    org_id = uuid4()
    org = Organization(id=org_id, name="Test Org")
    db_session.add(org)
    
    t_id = uuid4()
    tenant = Tenant(
        id=t_id, 
        name="Test Tenant", 
        organization_id=org_id,
        location_code=f"LOC-{t_id}"
    )
    db_session.add(tenant)
    await db_session.commit()
    return t_id

@pytest.fixture
async def setup_membership_data(db_session: AsyncSession, tenant_id: UUID):
    """Fixture to set up basic membership data."""
    # Create member
    member = Member(
        id=uuid4(),
        tenant_id=tenant_id,
        member_number="MEM-001",
        first_name="Test",
        last_name="Member",
        email="test@example.com",
    )
    db_session.add(member)
    await db_session.commit()
    
    # Create plan and version
    plan = Plan(id=uuid4(), tenant_id=tenant_id, name="Pro Plan")
    db_session.add(plan)
    await db_session.commit()
    
    plan_version = PlanVersion(
        id=uuid4(),
        tenant_id=tenant_id,
        plan_id=plan.id,
        version=1,
        price_amount_minor=5000,
        billing_cycle_months=1,
    )
    db_session.add(plan_version)
    await db_session.commit()
    
    # Create membership
    membership = Membership(
        id=uuid4(),
        tenant_id=tenant_id,
        member_id=member.id,
        plan_version_id=plan_version.id,
        status="ACTIVE",
        start_date=datetime.now(UTC),
    )
    db_session.add(membership)
    
    await db_session.commit()
    await db_session.refresh(membership)
    
    return membership

@pytest.mark.asyncio
async def test_freeze_membership_success(db_session: AsyncSession, setup_membership_data: Membership):
    membership = setup_membership_data
    service = MembershipService(db_session)
    
    start_date = datetime.now(UTC)
    expected_end_date = start_date + timedelta(days=30)
    
    freeze = await service.freeze_membership(
        membership_id=membership.id,
        start_date=start_date,
        expected_end_date=expected_end_date,
        reason="Vacation"
    )
    
    # Verify freeze record
    assert freeze is not None
    assert freeze.membership_id == membership.id
    assert freeze.reason == "Vacation"
    assert freeze.actual_end_date is None
    
    # Verify membership status changed
    await db_session.refresh(membership)
    assert membership.status == "FROZEN"
    
@pytest.mark.asyncio
async def test_unfreeze_membership_success(db_session: AsyncSession, setup_membership_data: Membership):
    membership = setup_membership_data
    service = MembershipService(db_session)
    
    start_date = datetime.now(UTC)
    expected_end_date = start_date + timedelta(days=30)
    
    # Freeze it first
    await service.freeze_membership(
        membership_id=membership.id,
        start_date=start_date,
        expected_end_date=expected_end_date,
        reason="Vacation"
    )
    
    # Unfreeze it
    unfrozen_membership = await service.unfreeze_membership(
        membership_id=membership.id
    )
    
    # Verify membership status is ACTIVE
    assert unfrozen_membership.status == "ACTIVE"
