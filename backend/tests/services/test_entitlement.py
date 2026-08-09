import asyncio
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.member import Member
from app.models.tenant import Tenant
from app.models.organization import Organization


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
async def member(db_session, setup_tenant):
    m = Member(
        id=uuid4(),
        tenant_id=setup_tenant.id,
        member_number=f"MEM-{uuid4().hex[:6]}",
        first_name="Test",
        last_name="Member",
        email=f"test-{uuid4()}@example.com",
    )
    db_session.add(m)
    await db_session.commit()
    return m


from app.models.entitlement import (
    EntitlementDefinition,
    EntitlementType,
    EntitlementWallet,
)
from app.services.entitlement import EntitlementService


@pytest.mark.asyncio
async def test_entitlement_zero_balance(db_session, setup_tenant, member):
    # RLS fixture implies db_session is authenticated as tenant
    def_id = uuid4()
    wallet_id = uuid4()
    db_session.add(EntitlementDefinition(id=def_id, tenant_id=setup_tenant.id, code="PT_SESSION", name="PT", type=EntitlementType.COUNT))
    db_session.add(EntitlementWallet(id=wallet_id, tenant_id=setup_tenant.id, member_id=member.id, entitlement_id=def_id, remaining=0))
    await db_session.commit()
    
    res = await EntitlementService.consume_access(db_session, setup_tenant.id, member.id, "PT_SESSION", "idem1")
    assert res["granted"] is False
    assert res["reason"] == "ZERO_BALANCE"

@pytest.mark.asyncio
async def test_entitlement_concurrent_double_consume(db_session, setup_tenant, member):
    def_id = uuid4()
    wallet_id = uuid4()
    db_session.add(EntitlementDefinition(id=def_id, tenant_id=setup_tenant.id, code="PT_SESSION", name="PT", type=EntitlementType.COUNT))
    db_session.add(EntitlementWallet(id=wallet_id, tenant_id=setup_tenant.id, member_id=member.id, entitlement_id=def_id, remaining=1))
    await db_session.commit()

    async def consume(idem):
        return await EntitlementService.consume_access(db_session, setup_tenant.id, member.id, "PT_SESSION", idem)
    
    # Run two consumes concurrently
    res1, res2 = await asyncio.gather(consume("idem2"), consume("idem3"))
    
    # Only one should succeed
    successes = sum(1 for r in [res1, res2] if r["granted"])
    assert successes == 1

