"""Phase 15.5B: outbox lease fencing + inbox handler atomicity."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.organization import Organization
from app.models.outbox import InboxEvent, OutboxEvent
from app.models.tenant import Tenant
from app.services.outbox import OutboxService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Fence Org", domain=f"fn-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="Fence T",
        organization_id=org.id,
        location_code=f"FN-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


@pytest.mark.asyncio
async def test_stale_worker_cannot_publish_or_fail(db_session, tenant):
    svc = OutboxService(db_session)
    await svc.enqueue(tenant.id, "test.job.v1", {"n": 1}, wrap_envelope=False)
    await db_session.commit()

    c1 = await svc.claim_pending(tenant_id=tenant.id, worker_id="w1")
    await db_session.commit()
    assert c1[0].worker_id == "w1"

    row = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.tenant_id == tenant.id)
        )
    ).scalar_one()
    row.lease_until = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.commit()

    c2 = await svc.claim_pending(tenant_id=tenant.id, worker_id="w2")
    await db_session.commit()
    assert c2[0].worker_id == "w2"

    # Stale W1 must fail CAS
    with pytest.raises(ValueError, match="lease_ownership_lost"):
        await svc.mark_published(c1[0], worker_id="w1")
    with pytest.raises(ValueError, match="lease_ownership_lost"):
        await svc.mark_failed(c1[0], "x", worker_id="w1")

    await svc.mark_published(c2[0], worker_id="w2")
    await db_session.commit()
    row = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.tenant_id == tenant.id)
        )
    ).scalar_one()
    assert row.status == "PUBLISHED"


@pytest.mark.asyncio
async def test_inbox_handler_savepoint_rolls_back_domain(db_session, tenant):
    svc = OutboxService(db_session)
    await svc.receive_inbox(tenant.id, event_id="e-atom", event_type="h.v1", payload={})
    await db_session.commit()
    side = f"side-{uuid4().hex}.com"

    async def bad_handler(db, _ev):
        db.add(Organization(name="Leak", domain=side))
        await db.flush()
        raise RuntimeError("handler boom")

    stats = await svc.process_pending_inbox(tenant.id, {"h.v1": bad_handler})
    await db_session.commit()
    assert stats["failed"] == 1

    leak = (
        await db_session.execute(
            select(Organization).where(Organization.domain == side)
        )
    ).scalar_one_or_none()
    assert leak is None

    row = (
        await db_session.execute(
            select(InboxEvent).where(InboxEvent.tenant_id == tenant.id)
        )
    ).scalar_one()
    assert row.status == "FAILED"


@pytest.mark.asyncio
async def test_inbox_handler_sql_error_still_marks_failed(db_session, tenant):
    svc = OutboxService(db_session)
    await svc.receive_inbox(
        tenant.id, event_id="e-sql", event_type="sql.v1", payload={}
    )
    await db_session.commit()

    async def sql_boom(db, _ev):
        await db.execute(text("SELECT 1 FROM definitely_no_such_table_xyz"))

    stats = await svc.process_pending_inbox(tenant.id, {"sql.v1": sql_boom})
    await db_session.commit()
    assert stats["failed"] == 1
    row = (
        await db_session.execute(
            select(InboxEvent).where(InboxEvent.event_id == "e-sql")
        )
    ).scalar_one()
    assert row.status == "FAILED"
