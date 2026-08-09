"""Phase 15.5 outbox lease reclaim + inbox retry."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
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
    org = Organization(name="Lease Org", domain=f"ls-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="Lease T",
        organization_id=org.id,
        location_code=f"LS-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


@pytest.mark.asyncio
async def test_stale_processing_reclaim(db_session, tenant):
    svc = OutboxService(db_session)
    await svc.enqueue(
        tenant.id, "job.v1", {"n": 1}, wrap_envelope=False, dedupe_key="d1"
    )
    await db_session.commit()

    claimed = await svc.claim_pending(
        tenant_id=tenant.id, worker_id="w1", lease_seconds=30
    )
    assert len(claimed) == 1
    assert claimed[0].status == "PROCESSING"
    assert claimed[0].worker_id == "w1"
    await db_session.commit()

    # Expire lease
    row = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.tenant_id == tenant.id)
        )
    ).scalar_one()
    row.lease_until = datetime.now(UTC) - timedelta(seconds=5)
    await db_session.commit()

    reclaimed = await svc.claim_pending(
        tenant_id=tenant.id, worker_id="w2", lease_seconds=30
    )
    assert len(reclaimed) == 1
    assert reclaimed[0].worker_id == "w2"
    await db_session.commit()


@pytest.mark.asyncio
async def test_inbox_failed_retry(db_session, tenant):
    svc = OutboxService(db_session)
    await svc.receive_inbox(
        tenant.id, event_id="e1", event_type="hook.v1", payload={"a": 1}
    )
    await db_session.commit()

    async def boom(_db, _ev):
        raise RuntimeError("transient")

    stats = await svc.process_pending_inbox(
        tenant.id, {"hook.v1": boom}, max_attempts=5, retry_after_seconds=1
    )
    await db_session.commit()
    assert stats["failed"] == 1

    row = (
        await db_session.execute(
            select(InboxEvent).where(InboxEvent.tenant_id == tenant.id)
        )
    ).scalar_one()
    assert row.status == "FAILED"
    assert row.available_at is not None

    # Make available now
    row.available_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.commit()

    calls = {"n": 0}

    async def ok(_db, _ev):
        calls["n"] += 1

    stats2 = await svc.process_pending_inbox(tenant.id, {"hook.v1": ok})
    await db_session.commit()
    assert stats2["processed"] == 1
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_enqueue_wraps_envelope(db_session, tenant):
    svc = OutboxService(db_session)
    r = await svc.enqueue(tenant.id, "membership.renewed.v1", {"m": "1"})
    await db_session.commit()
    assert r.event.payload.get("specversion") == "1.0"
    assert r.event.payload.get("type") == "membership.renewed.v1"
    assert r.event.payload.get("data", {}).get("m") == "1"
