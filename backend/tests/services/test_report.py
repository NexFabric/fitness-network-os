"""Phase 16 report service — real PostgreSQL tests."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.event_types import REPORT_RUN_REQUESTED_V1
from app.models.organization import Organization
from app.models.outbox import OutboxEvent
from app.models.report import (
    REPORT_STATUS_PENDING,
    REPORT_STATUS_SUCCEEDED,
    ReportRun,
)
from app.models.tenant import Tenant
from app.services.outbox import OutboxService
from app.services.report import ReportService, outbox_report_run_requested_handler


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Report Org", domain=f"rpt-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="Report Tenant",
        organization_id=org.id,
        location_code=f"R-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


@pytest.mark.asyncio
async def test_create_definition_and_request_run_pending_outbox(db_session, tenant):
    svc = ReportService(db_session)
    defn = await svc.create_definition(
        tenant.id,
        code="monthly_revenue",
        name="Monthly Revenue",
        report_type="REVENUE",
        config={"period": "month"},
    )
    await db_session.commit()
    assert defn.code == "monthly_revenue"
    assert defn.is_active is True

    result = await svc.request_run(
        tenant.id,
        definition_code="monthly_revenue",
        parameters={"month": "2026-08"},
        export_format="JSON",
        enqueue_outbox=True,
    )
    await db_session.commit()

    assert result.created is True
    run = result.run
    assert run.status == REPORT_STATUS_PENDING
    assert run.definition_id == defn.id
    assert run.parameters == {"month": "2026-08"}
    assert run.export_format == "JSON"

    rows = (
        (
            await db_session.execute(
                select(OutboxEvent).where(
                    OutboxEvent.tenant_id == tenant.id,
                    OutboxEvent.event_type == REPORT_RUN_REQUESTED_V1,
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    ev = rows[0]
    assert ev.status == "PENDING"
    assert ev.aggregate_type == "report_run"
    assert ev.aggregate_id == run.id
    payload = ev.payload
    assert isinstance(payload, dict)
    data = payload.get("data", payload)
    assert data.get("run_id") == str(run.id)
    assert data.get("definition_code") == "monthly_revenue"


@pytest.mark.asyncio
async def test_execute_run_succeeded_with_result_url(db_session, tenant):
    svc = ReportService(db_session)
    await svc.create_definition(
        tenant.id,
        code="members_export",
        name="Members Export",
        report_type="GENERIC",
    )
    await db_session.commit()

    requested = await svc.request_run(
        tenant.id,
        definition_code="members_export",
        enqueue_outbox=False,
    )
    await db_session.commit()
    assert requested.run.status == REPORT_STATUS_PENDING

    run = await svc.execute_run(tenant.id, requested.run.id)
    await db_session.commit()

    assert run.status == REPORT_STATUS_SUCCEEDED
    assert run.result_url == f"memory://reports/{tenant.id}/{run.id}"
    assert run.started_at is not None
    assert run.finished_at is not None
    assert run.row_count == 0
    assert run.error_message is None

    # Idempotent re-execute keeps SUCCEEDED
    again = await svc.execute_run(tenant.id, run.id)
    await db_session.commit()
    assert again.status == REPORT_STATUS_SUCCEEDED
    assert again.result_url == run.result_url


@pytest.mark.asyncio
async def test_request_run_dedupe_key_idempotent(db_session, tenant):
    svc = ReportService(db_session)
    await svc.create_definition(
        tenant.id,
        code="dedupe_rpt",
        name="Dedupe Report",
    )
    await db_session.commit()

    a = await svc.request_run(
        tenant.id,
        definition_code="dedupe_rpt",
        dedupe_key="nightly:2026-08-10",
        enqueue_outbox=False,
    )
    await db_session.commit()
    b = await svc.request_run(
        tenant.id,
        definition_code="dedupe_rpt",
        dedupe_key="nightly:2026-08-10",
        enqueue_outbox=False,
    )
    await db_session.commit()

    assert a.created is True
    assert b.created is False
    assert a.run.id == b.run.id

    count = (
        (
            await db_session.execute(
                select(ReportRun).where(ReportRun.tenant_id == tenant.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(count) == 1


@pytest.mark.asyncio
async def test_outbox_handler_executes_run(db_session, tenant):
    """Optional path: claim + dispatch report.run.requested.v1 → SUCCEEDED."""
    svc = ReportService(db_session)
    await svc.create_definition(
        tenant.id,
        code="via_outbox",
        name="Via Outbox",
    )
    await db_session.commit()

    requested = await svc.request_run(
        tenant.id,
        definition_code="via_outbox",
        enqueue_outbox=True,
    )
    await db_session.commit()
    run_id = requested.run.id

    outbox = OutboxService(db_session)
    claimed = await outbox.claim_pending(tenant_id=tenant.id, worker_id="w-rpt-pub")
    await db_session.commit()
    assert len(claimed) == 1
    assert claimed[0].event_type == REPORT_RUN_REQUESTED_V1

    async def publisher(ev: OutboxEvent) -> None:
        await outbox_report_run_requested_handler(db_session, ev)

    stats = await outbox.dispatch_claimed(claimed, publisher, worker_id="w-rpt-pub")
    await db_session.commit()
    assert stats["published"] == 1

    run = (
        await db_session.execute(select(ReportRun).where(ReportRun.id == run_id))
    ).scalar_one()
    assert run.status == REPORT_STATUS_SUCCEEDED
    assert run.result_url is not None
