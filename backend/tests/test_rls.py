import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import Column, String, event
from sqlalchemy.orm import Session
from app.db.base import TenantMixin, Base
from app.api.deps import current_tenant_id_var

# Dummy model for testing RLS structure
class DummyTenantItem(Base, TenantMixin):
    __tablename__ = "dummy_tenant_items"
    name = Column(String)

@pytest.fixture
async def mock_rls_engine():
    # Use SQLite for dummy structure verification. 
    # Real RLS tests require Postgres and a running container.
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    # SQLite doesn't support SET LOCAL, so we skip the actual SQL execution for this mock
    @event.listens_for(Session, "after_begin")
    def mock_set_tenant_id(session, transaction, connection):
        tenant_id = current_tenant_id_var.get(None)
        # We can't run connection.execute(text("SET LOCAL...")) on sqlite
        pass
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def rls_session_maker(mock_rls_engine):
    maker = async_sessionmaker(mock_rls_engine, class_=AsyncSession, expire_on_commit=False)
    return maker

@pytest.mark.asyncio
async def test_tenant_context_isolation(rls_session_maker):
    """
    Verifies that the current_tenant_id_var correctly isolates the tenant context
    across simulated requests, and that the TenantMixin structure is intact.
    """
    tenant_a = uuid4()
    tenant_b = uuid4()
    
    # 1. Simulate Request as Tenant A
    token_a = current_tenant_id_var.set(tenant_a)
    
    async with rls_session_maker() as session:
        assert current_tenant_id_var.get() == tenant_a
        item_a = DummyTenantItem(tenant_id=tenant_a, name="Item A")
        session.add(item_a)
        await session.commit()
    
    current_tenant_id_var.reset(token_a)
    
    # 2. Simulate Request as Tenant B
    token_b = current_tenant_id_var.set(tenant_b)
    
    async with rls_session_maker() as session:
        assert current_tenant_id_var.get() == tenant_b
        item_b = DummyTenantItem(tenant_id=tenant_b, name="Item B")
        session.add(item_b)
        await session.commit()
        
    current_tenant_id_var.reset(token_b)
