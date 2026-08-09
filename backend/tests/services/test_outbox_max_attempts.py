"""Phase 15.5D P1-A: outbox claim max_attempts crash-loop protection."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.organization import Organization
from app.models.outbox import OutboxEvent
from app.models.tenant import Tenant
from app.services.outbox import OutboxService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="MaxAtt Org", domain=f"ma-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="MaxAtt T",
        organization_id=org.id,
        location_code=f"MA-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


async def _expire_lease(db_session: AsyncSession, tenant_id) -> OutboxEvent:
    row = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.tenant_id == tenant_id)
        )
    ).scalar_one()
    row.lease_until = datetime.now(UTC) - timedelta(seconds=5)
    await db_session.commit()
    return row


@pytest.mark.asyncio
async def test_crash_loop_stops_at_max_attempts(db_session, tenant):
    """Worker crash after claim without mark_failed must not reclaim forever."""
    svc = OutboxService(db_session)
    max_attempts = 3
    await svc.enqueue(
        tenant.id, "test.job.v1", {"n": 1}, wrap_envelope=False, dedupe_key="crash-1"
    )
    await db_session.commit()

    for i in range(max_attempts):
        claimed = await svc.claim_pending(
            tenant_id=tenant.id,
            worker_id=f"crash-w{i}",
            max_attempts=max_attempts,
        )
        await db_session.commit()
        assert len(claimed) == 1, f"expected claim on attempt {i + 1}"
        assert claimed[0].attempt_count == i + 1
        assert claimed[0].status == "PROCESSING"
        # Crash: no mark_failed / mark_published — only expire lease.
        await _expire_lease(db_session, tenant.id)

    # Further claim must not reclaim; row moves to DEAD (exhausted stale PROCESSING).
    tenant_id = tenant.id
    empty = await svc.claim_pending(
        tenant_id=tenant_id,
        worker_id="crash-w-final",
        max_attempts=max_attempts,
    )
    await db_session.commit()
    assert empty == []

    # Bulk DEAD update uses synchronize_session=fetch; refresh via expire on row class.
    db_session.expire_all()
    row = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.tenant_id == tenant_id)
        )
    ).scalar_one()
    assert row.status == "DEAD"
    assert row.attempt_count == max_attempts
    assert row.error_message == "max_attempts_exceeded_on_claim"
    assert row.worker_id is None
    assert row.lease_until is None

    # Still not claimable after DEAD.
    empty2 = await svc.claim_pending(
        tenant_id=tenant_id, worker_id="crash-w-again", max_attempts=max_attempts
    )
    await db_session.commit()
    assert empty2 == []


@pytest.mark.asyncio
async def test_mark_failed_below_and_at_max_attempts(db_session, tenant):
    """Normal publisher failure path: FAILED while under cap, DEAD at max."""
    svc = OutboxService(db_session)
    max_attempts = 3
    await svc.enqueue(
        tenant.id, "test.job.v1", {"n": 2}, wrap_envelope=False, dedupe_key="fail-path"
    )
    await db_session.commit()

    # Attempt 1 → FAILED (retriable)
    c1 = await svc.claim_pending(
        tenant_id=tenant.id, worker_id="w-f1", max_attempts=max_attempts
    )
    await db_session.commit()
    assert len(c1) == 1
    await svc.mark_failed(
        c1[0],
        "transient",
        worker_id="w-f1",
        max_attempts=max_attempts,
        retry_after_seconds=1,
    )
    await db_session.commit()
    row = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.tenant_id == tenant.id)
        )
    ).scalar_one()
    assert row.status == "FAILED"
    assert row.attempt_count == 1
    assert row.available_at is not None

    # Make available now
    row.available_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.commit()

    # Attempt 2 → still FAILED
    c2 = await svc.claim_pending(
        tenant_id=tenant.id, worker_id="w-f2", max_attempts=max_attempts
    )
    await db_session.commit()
    await svc.mark_failed(
        c2[0],
        "still_transient",
        worker_id="w-f2",
        max_attempts=max_attempts,
        retry_after_seconds=1,
    )
    await db_session.commit()
    row = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.tenant_id == tenant.id)
        )
    ).scalar_one()
    assert row.status == "FAILED"
    assert row.attempt_count == 2

    row.available_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.commit()

    # Attempt 3 (at max) → DEAD
    c3 = await svc.claim_pending(
        tenant_id=tenant.id, worker_id="w-f3", max_attempts=max_attempts
    )
    await db_session.commit()
    assert c3[0].attempt_count == 3
    await svc.mark_failed(
        c3[0],
        "give_up",
        worker_id="w-f3",
        max_attempts=max_attempts,
    )
    await db_session.commit()
    row = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.tenant_id == tenant.id)
        )
    ).scalar_one()
    assert row.status == "DEAD"
    assert row.attempt_count == 3
    assert row.error_message == "give_up"

    empty = await svc.claim_pending(
        tenant_id=tenant.id, worker_id="w-f4", max_attempts=max_attempts
    )
    await db_session.commit()
    assert empty == []
