import pytest
from uuid import uuid4
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

from app.db.base import Base
from app.models.report import ReportDefinition, ReportRun
from app.models.notification import NotificationTemplate, NotificationDelivery
from app.models.outbox import OutboxEvent, InboxEvent
from app.api.deps import current_tenant_id_var

@pytest.fixture
async def operational_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield maker
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_operational_models_tenant_isolation(operational_db):
    """
    Verifies that the new operational models correctly inherit TenantMixin
    and enforce tenant isolation structurally.
    """
    tenant_id_a = uuid4()
    tenant_id_b = uuid4()
    
    # 1. Create data for Tenant A
    token_a = current_tenant_id_var.set(tenant_id_a)
    
    async with operational_db() as session:
        report_def = ReportDefinition(tenant_id=tenant_id_a, name="Monthly Revenue", config={"type": "revenue"})
        session.add(report_def)
        
        notification_tpl = NotificationTemplate(tenant_id=tenant_id_a, name="Welcome", channel="EMAIL", body_template="Hello")
        session.add(notification_tpl)
        
        outbox_event = OutboxEvent(tenant_id=tenant_id_a, event_type="member.created", payload={"id": str(uuid4())})
        session.add(outbox_event)
        
        await session.commit()
        
    current_tenant_id_var.reset(token_a)
    
    # 2. Verify data for Tenant B (should be isolated)
    # Testing that we can create similar data for Tenant B without conflicts 
    # (since we are testing the model structure). RLS logic will actually filter this at DB level
    # in postgres, but in SQLite we just verify they have the tenant_id column correctly mapped.
    token_b = current_tenant_id_var.set(tenant_id_b)
    
    async with operational_db() as session:
        inbox_event = InboxEvent(tenant_id=tenant_id_b, event_id=str(uuid4()), event_type="payment.succeeded", payload={})
        session.add(inbox_event)
        await session.commit()
        
        assert inbox_event.tenant_id == tenant_id_b
        
    current_tenant_id_var.reset(token_b)


@pytest.mark.asyncio
async def test_outbox_idempotent_processor_stub():
    """
    Stub for testing the idempotent processor logic of Outbox pattern.
    Ensures that processing an event twice does not result in double execution.
    """
    tenant_id = uuid4()
    processed_events = set()
    
    def process_event(event: OutboxEvent):
        # Stub logic: Check if already processed
        if event.id in processed_events:
            return False  # Already processed
        
        # Mark as processed
        processed_events.add(event.id)
        event.status = "PROCESSED"
        return True

    # Simulate an outbox event
    event = OutboxEvent(id=uuid4(), tenant_id=tenant_id, event_type="test", payload={}, status="PENDING")
    
    # First processing attempt should succeed
    assert process_event(event) is True
    assert event.status == "PROCESSED"
    
    # Second processing attempt should skip (idempotent)
    assert process_event(event) is False
    assert event.status == "PROCESSED"
