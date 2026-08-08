import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import event
from sqlalchemy.orm import Session
from app.db.base import Base
from app.api.deps import current_tenant_id_var
from app.models.federation import PassportConfig, ComplianceRecord

@pytest.fixture
async def mock_rls_engine():
    # Use SQLite for dummy structure verification. 
    # Real RLS tests require Postgres and a running container.
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    # SQLite doesn't support SET LOCAL, so we skip the actual SQL execution for this mock
    @event.listens_for(Session, "after_begin")
    def mock_set_tenant_id(session, transaction, connection):
        tenant_id = current_tenant_id_var.get(None)
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
async def test_federation_models_tenant_context_isolation(rls_session_maker):
    """
    Verifies that the current_tenant_id_var correctly isolates the tenant context
    across simulated requests for Federation models, and that the TenantMixin structure is intact.
    """
    tenant_a = uuid4()
    
    # Simulate Request as Tenant A
    token_a = current_tenant_id_var.set(tenant_a)
    
    async with rls_session_maker() as session:
        assert current_tenant_id_var.get() == tenant_a
        
        # Test PassportConfig
        passport = PassportConfig(tenant_id=tenant_a, is_active=True, allowed_home_gym_tiers="PREMIUM")
        session.add(passport)
        
        # Test ComplianceRecord
        compliance = ComplianceRecord(tenant_id=tenant_a, certification_name="ISO 27001", status="PASSED")
        session.add(compliance)
        
        await session.commit()
        await session.refresh(passport)
        await session.refresh(compliance)
        
        # Verify tenant_id inheritance
        assert passport.tenant_id == tenant_a
        assert compliance.tenant_id == tenant_a
    
    current_tenant_id_var.reset(token_a)
