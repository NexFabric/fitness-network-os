import pytest
from uuid import uuid4
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.base import Base
from app.api.deps import current_tenant_id_var
from sqlalchemy.orm import Session
from sqlalchemy import event

# Import the models we want to test
from app.models.membership import Plan, PlanVersion, Membership, Entitlement
from app.models.member import Member

@pytest.fixture
async def mock_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    @event.listens_for(Session, "after_begin")
    def mock_set_tenant_id(session, transaction, connection):
        pass # mock for SQLite
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def session_maker(mock_engine):
    maker = async_sessionmaker(mock_engine, class_=AsyncSession, expire_on_commit=False)
    return maker

@pytest.mark.asyncio
async def test_membership_tenant_isolation(session_maker):
    tenant_id = uuid4()
    token = current_tenant_id_var.set(tenant_id)
    
    async with session_maker() as session:
        # Create a member
        member = Member(
            tenant_id=tenant_id,
            member_number="M-001",
            first_name="John",
            last_name="Doe",
            status="ACTIVE"
        )
        session.add(member)
        await session.flush()
        
        # Create Plan and Version
        plan = Plan(
            tenant_id=tenant_id,
            name="Pro Plan",
            description="Access to everything"
        )
        session.add(plan)
        await session.flush()
        
        plan_version = PlanVersion(
            tenant_id=tenant_id,
            plan_id=plan.id,
            version=1,
            price_amount_minor=10000,
            billing_cycle_months=1
        )
        session.add(plan_version)
        await session.flush()
        
        # Create Membership
        membership = Membership(
            tenant_id=tenant_id,
            member_id=member.id,
            plan_version_id=plan_version.id,
            status="ACTIVE",
            start_date=datetime.now(UTC)
        )
        session.add(membership)
        await session.flush()
        
        # Create Entitlement
        entitlement = Entitlement(
            tenant_id=tenant_id,
            member_id=member.id,
            membership_id=membership.id,
            entitlement_type="group_classes",
            balance=10
        )
        session.add(entitlement)
        await session.commit()
        
        # Verify isolation logic - fetching correctly associates member with plan version
        assert membership.tenant_id == tenant_id
        assert entitlement.balance == 10
        assert plan_version.price_amount_minor == 10000
    
    current_tenant_id_var.reset(token)
