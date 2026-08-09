from uuid import uuid4

import pytest
from sqlalchemy import Column, String, select, text

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
    # 1. Create table and enable RLS on the table
    async with pg_engine.begin() as conn:
        await conn.run_sync(DummyTenantItem.__table__.create, checkfirst=True)
        await conn.execute(text("ALTER TABLE dummy_tenant_items ENABLE ROW LEVEL SECURITY;"))
        await conn.execute(text("DROP POLICY IF EXISTS tenant_isolation_policy ON dummy_tenant_items;"))
        await conn.execute(text(
            "CREATE POLICY tenant_isolation_policy ON dummy_tenant_items "
            "AS PERMISSIVE FOR ALL "
            "TO PUBLIC "
            "USING (tenant_id = nullif(current_setting('app.current_tenant_id', true), '')::uuid) "
            "WITH CHECK (tenant_id = nullif(current_setting('app.current_tenant_id', true), '')::uuid);"
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

    # Test Spoofed INSERT (Tenant A tries to insert for Tenant B)
    token_a = current_tenant_id_var.set(tenant_a)
    async with pg_session_maker() as session:
        
        # Test INSERT for Tenant B
        try:
            spoofed_item = DummyTenantItem(tenant_id=tenant_b, name="Spoofed Item")
            session.add(spoofed_item)
            await session.commit()
            assert False, "Should have raised RLS error on spoofed insert"
        except Exception as e:
            await session.rollback()
            assert "new row violates row-level security policy" in str(e) or "row violates row-level security" in str(e) or "violates row-level security policy" in str(e)

        # Get the ID of B's item to test UPDATE and DELETE
        # We need to switch context to B to get it
        current_tenant_id_var.set(tenant_b)
        await session.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_b}';"))
        res = await session.execute(select(DummyTenantItem).where(DummyTenantItem.name == "Item B1"))
        b_item = res.scalars().first()
        b_id = b_item.id
        
        # Switch back to A
        current_tenant_id_var.set(tenant_a)
        await session.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_a}';"))

        # Test UPDATE on Tenant B's data
        from sqlalchemy import delete, update
        upd_res = await session.execute(
            update(DummyTenantItem)
            .where(DummyTenantItem.id == b_id)
            .values(name="Hacked Name")
        )
        assert upd_res.rowcount == 0, "Should not be able to update another tenant's row"
        
        # Test DELETE on Tenant B's data
        del_res = await session.execute(
            delete(DummyTenantItem)
            .where(DummyTenantItem.id == b_id)
        )
        assert del_res.rowcount == 0, "Should not be able to delete another tenant's row"
        
        await session.commit()
        
    current_tenant_id_var.reset(token_a)
    
    # Test INSERT with missing context
    token_empty = current_tenant_id_var.set(None)
    async with pg_session_maker() as session:
        # Note: missing context means setting app.current_tenant_id is missing, but test setup uses empty session. 
        # By default the var might be unset or empty string. Let's explicitly clear it for the session
        await session.execute(text("SET LOCAL app.current_tenant_id = '';"))
        try:
            empty_item = DummyTenantItem(tenant_id=tenant_a, name="Empty Item")
            session.add(empty_item)
            await session.commit()
            assert False, "Should have raised RLS error on insert with no context"
        except Exception as e:
            await session.rollback()
            assert "new row violates row-level security policy" in str(e) or "violates row-level security" in str(e)

    current_tenant_id_var.reset(token_empty)
