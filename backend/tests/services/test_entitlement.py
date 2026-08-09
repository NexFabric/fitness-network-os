import asyncio
from uuid import uuid4
import pytest
from httpx import AsyncClient
from app.services.entitlement import EntitlementService
from app.models.entitlement import EntitlementWallet, EntitlementDefinition, EntitlementType

@pytest.mark.asyncio
async def test_entitlement_zero_balance(db_session, rls_tenant, member):
    # RLS fixture implies db_session is authenticated as tenant
    def_id = uuid4()
    wallet_id = uuid4()
    db_session.add(EntitlementDefinition(id=def_id, tenant_id=rls_tenant.id, code="PT_SESSION", name="PT", type=EntitlementType.COUNT))
    db_session.add(EntitlementWallet(id=wallet_id, tenant_id=rls_tenant.id, member_id=member.id, entitlement_id=def_id, remaining=0))
    await db_session.commit()
    
    res = await EntitlementService.consume_access(db_session, rls_tenant.id, member.id, "PT_SESSION", "idem1")
    assert res["granted"] is False
    assert res["reason"] == "ZERO_BALANCE"

@pytest.mark.asyncio
async def test_entitlement_concurrent_double_consume(db_session, rls_tenant, member):
    def_id = uuid4()
    wallet_id = uuid4()
    db_session.add(EntitlementDefinition(id=def_id, tenant_id=rls_tenant.id, code="PT_SESSION", name="PT", type=EntitlementType.COUNT))
    db_session.add(EntitlementWallet(id=wallet_id, tenant_id=rls_tenant.id, member_id=member.id, entitlement_id=def_id, remaining=1))
    await db_session.commit()

    async def consume(idem):
        return await EntitlementService.consume_access(db_session, rls_tenant.id, member.id, "PT_SESSION", idem)
    
    # Run two consumes concurrently
    res1, res2 = await asyncio.gather(consume("idem2"), consume("idem3"))
    
    # Only one should succeed
    successes = sum(1 for r in [res1, res2] if r["granted"])
    assert successes == 1

