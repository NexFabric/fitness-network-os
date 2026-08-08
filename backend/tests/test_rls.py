import pytest
from sqlalchemy import text, Column, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from app.api.deps import current_tenant_id_var
from app.db.base import Base, TenantMixin

# Dummy model for testing RLS structure
class DummyTenantItem(Base, TenantMixin):
    __tablename__ = "dummy_tenant_items"
    name = Column(String)

@pytest.mark.asyncio
async def test_tenant_context_isolation(pg_engine, pg_session_maker):
    """
    Verifies that the current_tenant_id_var correctly isolates the tenant context
    across simulated requests using real PostgreSQL RLS.
    """
    # 1. Enable RLS on the table
    async with pg_engine.begin() as conn:
        await conn.execute(text("ALTER TABLE dummy_tenant_items ENABLE ROW LEVEL SECURITY;"))
        await conn.execute(text("DROP POLICY IF EXISTS tenant_isolation_policy ON dummy_tenant_items;"))
        await conn.execute(text(
            "CREATE POLICY tenant_isolation_policy ON dummy_tenant_items "
            "AS PERMISSIVE FOR ALL "
            "TO PUBLIC "
            "USING (tenant_id = nullif(current_setting('app.current_tenant_id', true), '')::uuid);"
        ))
        # Force RLS for the table owner as well, just in case postgres user is owner
        await conn.execute(text("ALTER TABLE dummy_tenant_items FORCE ROW LEVEL SECURITY;"))

    tenant_a = uuid4()
    tenant_b = uuid4()

    # Insert data setting the tenant ID properly
    async with pg_session_maker() as session:
        await session.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_a}';"))
        item_a1 = DummyTenantItem(tenant_id=tenant_a, name="Item A1")
        item_a2 = DummyTenantItem(tenant_id=tenant_a, name="Item A2")
        session.add_all([item_a1, item_a2])
        await session.commit()

        await session.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_b}';"))
        item_b1 = DummyTenantItem(tenant_id=tenant_b, name="Item B1")
        session.add(item_b1)
        await session.commit()

    # Test Tenant A session
    token_a = current_tenant_id_var.set(tenant_a)
    async with pg_session_maker() as session:
        result = await session.execute(select(DummyTenantItem))
        items = result.scalars().all()
        assert len(items) == 2
        assert all(i.tenant_id == tenant_a for i in items)
    current_tenant_id_var.reset(token_a)

    # Test Tenant B session
    token_b = current_tenant_id_var.set(tenant_b)
    async with pg_session_maker() as session:
        result = await session.execute(select(DummyTenantItem))
        items = result.scalars().all()
        assert len(items) == 1
        assert all(i.tenant_id == tenant_b for i in items)
    current_tenant_id_var.reset(token_b)

    # Test Empty Tenant session
    token_empty = current_tenant_id_var.set(None)
    async with pg_session_maker() as session:
        result = await session.execute(select(DummyTenantItem))
        items = result.scalars().all()
        # Admin / No Tenant -> no rows visible if tenant is not set
        # Wait, if tenant_id is NULL in policy, nothing matches (UUID = NULL is false)
        assert len(items) == 0
    current_tenant_id_var.reset(token_empty)
