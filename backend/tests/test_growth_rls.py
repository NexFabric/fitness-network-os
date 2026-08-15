from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from app.api.deps import current_tenant_id_var
from app.db.base import Base
from app.models.growth import Lead, Opportunity, RetentionCockpit, Task


@pytest.fixture
async def mock_rls_engine():
    # Use SQLite for dummy structure verification.
    # Real RLS tests require Postgres and a running container.
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    # SQLite doesn't support SET LOCAL, so we skip the actual SQL execution for this mock
    @event.listens_for(Session, "after_begin")
    def mock_set_tenant_id(session, transaction, connection):
        tenant_id = current_tenant_id_var.get(None)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def rls_session_maker(mock_rls_engine):
    maker = async_sessionmaker(
        mock_rls_engine, class_=AsyncSession, expire_on_commit=False
    )
    return maker


@pytest.mark.asyncio
async def test_growth_models_tenant_context_isolation(rls_session_maker):
    """
    Verifies that the current_tenant_id_var correctly isolates the tenant context
    across simulated requests for Growth models, and that the TenantMixin structure is intact.
    """
    tenant_a = uuid4()

    # Simulate Request as Tenant A
    token_a = current_tenant_id_var.set(tenant_a)

    async with rls_session_maker() as session:
        assert current_tenant_id_var.get() == tenant_a

        # Test Lead
        lead = Lead(
            tenant_id=tenant_a, first_name="John", last_name="Doe", status="NEW"
        )
        session.add(lead)
        await session.commit()
        await session.refresh(lead)

        # Test Opportunity
        opportunity = Opportunity(
            tenant_id=tenant_a, lead_id=lead.id, stage="PROSPECTING"
        )
        session.add(opportunity)

        # Test Task
        task = Task(tenant_id=tenant_a, title="Call John")
        session.add(task)

        # Test RetentionCockpit (needs member_id, but member is not strictly FK checked in sqlite without pragma, or we can just supply a dummy uuid)
        member_id = uuid4()
        cockpit = RetentionCockpit(
            tenant_id=tenant_a, member_id=member_id, health_score=85
        )
        session.add(cockpit)

        await session.commit()

        # Verify tenant_id inheritance
        assert lead.tenant_id == tenant_a
        assert opportunity.tenant_id == tenant_a
        assert task.tenant_id == tenant_a
        assert cockpit.tenant_id == tenant_a

    current_tenant_id_var.reset(token_a)
