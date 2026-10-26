"""Tests for Outbox Worker under PostgreSQL RLS, concurrency, and savepoint rollbacks."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import current_tenant_id_var
from app.core.event_types import NOTIFICATION_REQUESTED_V1
from app.models.organization import Organization
from app.models.outbox import OutboxEvent
from app.models.tenant import Tenant, TenantStatus
from app.services.outbox import OutboxService
from app.workers.outbox import (
    OUTBOX_EVENT_HANDLERS,
    process_outbox_for_tenant,
    run_outbox_cycle,
)


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def multi_tenants(db_session: AsyncSession) -> tuple[Tenant, Tenant, Tenant]:
    org = Organization(name="Outbox RLS Org", domain=f"obx-rls-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()

    t_active1 = Tenant(
        id=uuid4(),
        organization_id=org.id,
        name="Active Gym 1",
        status=TenantStatus.ACTIVE.value,
        location_code=f"ACT1-{uuid4().hex[:4]}",
    )
    t_active2 = Tenant(
        id=uuid4(),
        organization_id=org.id,
        name="Active Gym 2",
        status=TenantStatus.ACTIVE.value,
        location_code=f"ACT2-{uuid4().hex[:4]}",
    )
    t_suspended = Tenant(
        id=uuid4(),
        organization_id=org.id,
        name="Suspended Gym",
        status=TenantStatus.SUSPENDED.value,
        location_code=f"SUS-{uuid4().hex[:4]}",
    )
    db_session.add_all([t_active1, t_active2, t_suspended])
    await db_session.commit()
    return t_active1, t_active2, t_suspended


@pytest.mark.asyncio
async def test_worker_cycle_processes_active_tenants_and_skips_suspended(
    db_session: AsyncSession, multi_tenants: tuple[Tenant, Tenant, Tenant]
):
    """Verifies that run_outbox_cycle iterates through active tenants under RLS and skips suspended."""
    t1, t2, t_sus = multi_tenants

    # Enqueue events for all 3 tenants under their respective RLS contexts
    for t in (t1, t2, t_sus):
        token = current_tenant_id_var.set(t.id)
        if db_session.bind and db_session.bind.dialect.name == "postgresql":
            await db_session.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, true)"),
                {"tid": str(t.id)},
            )
        svc = OutboxService(db_session)
        await svc.enqueue(
            t.id,
            "membership.activated.v1",
            {"membership_id": str(uuid4())},
            aggregate_type="membership",
        )
        await db_session.commit()
        current_tenant_id_var.reset(token)

    # Run one full worker cycle
    stats = await run_outbox_cycle(db_session, worker_id="worker-test-1")
    assert stats["outbox_published"] == 2
    assert stats["outbox_failed"] == 0

    # Verify T1 and T2 events are PUBLISHED
    for t in (t1, t2):
        token = current_tenant_id_var.set(t.id)
        if db_session.bind and db_session.bind.dialect.name == "postgresql":
            await db_session.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, true)"),
                {"tid": str(t.id)},
            )
        res = await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.tenant_id == t.id)
        )
        ev = res.scalars().one()
        assert ev.status == "PUBLISHED"
        assert ev.processed_at is not None
        current_tenant_id_var.reset(token)

    # Verify suspended tenant event remains PENDING
    token = current_tenant_id_var.set(t_sus.id)
    if db_session.bind and db_session.bind.dialect.name == "postgresql":
        await db_session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(t_sus.id)},
        )
    res_sus = await db_session.execute(
        select(OutboxEvent).where(OutboxEvent.tenant_id == t_sus.id)
    )
    ev_sus = res_sus.scalars().one()
    assert ev_sus.status == "PENDING"
    current_tenant_id_var.reset(token)


@pytest.mark.asyncio
async def test_handler_sql_error_savepoint_rollback_marks_failed(
    db_session: AsyncSession, multi_tenants: tuple[Tenant, Tenant, Tenant]
):
    """Verifies that an unhandled SQL exception inside a domain handler rolls back

    only the inner savepoint, allowing mark_failed to persist FAILED status without transaction abort.
    """
    t1, _, _ = multi_tenants
    token = current_tenant_id_var.set(t1.id)
    if db_session.bind and db_session.bind.dialect.name == "postgresql":
        await db_session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(t1.id)},
        )

    svc = OutboxService(db_session)
    enq = await svc.enqueue(t1.id, NOTIFICATION_REQUESTED_V1, {"data": 123})
    await db_session.commit()

    orig_handler = OUTBOX_EVENT_HANDLERS.get(NOTIFICATION_REQUESTED_V1)

    # Register a failing handler that causes a database error (e.g. invalid SQL or broken table)
    async def bad_sql_handler(db: AsyncSession, event: OutboxEvent):
        await db.execute(
            text("SELECT * FROM non_existent_table_that_throws_sql_error;")
        )

    OUTBOX_EVENT_HANDLERS[NOTIFICATION_REQUESTED_V1] = bad_sql_handler
    try:
        stats = await process_outbox_for_tenant(
            db_session, t1.id, worker_id="worker-sql-test"
        )
        await db_session.commit()

        assert stats["claimed"] == 1
        assert stats["failed"] == 1
        assert stats["published"] == 0

        # Verify the event transitioned to FAILED (not aborted)
        res = await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.id == enq.event.id)
        )
        row = res.scalars().one()
        assert row.status == "FAILED"
        assert row.attempt_count == 1
        assert "non_existent_table" in (row.error_message or "")
    finally:
        if orig_handler:
            OUTBOX_EVENT_HANDLERS[NOTIFICATION_REQUESTED_V1] = orig_handler
        else:
            OUTBOX_EVENT_HANDLERS.pop(NOTIFICATION_REQUESTED_V1, None)
        current_tenant_id_var.reset(token)
