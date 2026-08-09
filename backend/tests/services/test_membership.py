from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member
from app.models.membership import (
    Membership,
    Plan,
    PlanVersion,
)
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.services.membership import MembershipService


@pytest.fixture
async def db_session(pg_session_maker) -> AsyncGenerator[AsyncSession, None]:
    async with pg_session_maker() as session:
        yield session

@pytest.fixture
async def tenant_id(pg_engine) -> UUID:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    async_session = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        org_id = uuid4()
        org = Organization(id=org_id, name="Test Org")
        db.add(org)

    
        t_id = uuid4()
        tenant = Tenant(
            id=t_id, 
            name="Test Tenant", 
            organization_id=org_id,
            location_code=f"LOC-{t_id}"
        )
        db.add(tenant)
        await db.commit()
        return t_id

@pytest.fixture
async def setup_membership_data(pg_engine, tenant_id: UUID):
    """Fixture to set up basic membership data."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    async_session = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        # Create member
        member = Member(
            id=uuid4(),
            tenant_id=tenant_id,
            member_number="MEM-001",
            first_name="Test",
            last_name="Member",
            email="test@example.com",
        )
        db.add(member)
        await db.commit()
        
        # Create plan and version
        plan = Plan(id=uuid4(), tenant_id=tenant_id, name="Pro Plan")
        db.add(plan)
        await db.commit()
    
        plan_version = PlanVersion(
            id=uuid4(),
            tenant_id=tenant_id,
            plan_id=plan.id,
            version=1,
            price_amount_minor=5000,
            billing_cycle_months=1,
        )
        db.add(plan_version)
        await db.commit()
        
        # Create membership
        membership = Membership(
            id=uuid4(),
            tenant_id=tenant_id,
            member_id=member.id,
            plan_version_id=plan_version.id,
            status="ACTIVE",
            start_date=datetime.now(UTC),
        )
        db.add(membership)
        
        await db.commit()
        await db.refresh(membership)
        
        return membership

@pytest.mark.asyncio
async def test_freeze_membership_success(db_session: AsyncSession, setup_membership_data: Membership):
    membership = setup_membership_data
    from app.api.deps import current_tenant_id_var
    current_tenant_id_var.set(membership.tenant_id)
    
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
    m = await service.get_membership(membership.id)
    assert m is not None
    assert m.status == "FROZEN"
    
@pytest.mark.asyncio
async def test_unfreeze_membership_success(db_session: AsyncSession, setup_membership_data: Membership):
    membership = setup_membership_data
    from app.api.deps import current_tenant_id_var
    current_tenant_id_var.set(membership.tenant_id)
    
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
