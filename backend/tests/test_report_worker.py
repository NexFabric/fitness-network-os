"""Report worker cycle: empty queue and one pending run."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.organization import Organization
from app.models.report import REPORT_STATUS_PENDING, REPORT_STATUS_SUCCEEDED, ReportRun
from app.models.tenant import Tenant, TenantStatus
from app.services.report import ReportService
from app.workers.report import run_cycle


@pytest.mark.asyncio
async def test_report_run_cycle_on_empty_queue(pg_session_maker):
    with patch("app.workers.report.AsyncSessionLocal", pg_session_maker):
        processed = await run_cycle()
    assert processed == 0


@pytest.mark.asyncio
async def test_report_run_cycle_executes_pending(pg_engine, pg_session_maker):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Rpt Wkr Org", domain=f"rptw-{uuid4().hex[:8]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Rpt Wkr Tenant",
            organization_id=org.id,
            location_code=f"RW-{uuid4().hex[:6]}",
            status=TenantStatus.ACTIVE.value,
        )
        db.add(tenant)
        await db.flush()
        svc = ReportService(db)
        defn = await svc.create_definition(
            tenant.id, code="wkr_daily", name="Worker daily"
        )
        result = await svc.request_run(
            tenant.id,
            definition_code=defn.code,
            enqueue_outbox=False,
        )
        run_id = result.run.id
        await db.commit()

    with patch("app.workers.report.AsyncSessionLocal", pg_session_maker):
        processed = await run_cycle()
    assert processed == 1

    async with maker() as db:
        row = await db.get(ReportRun, run_id)
        assert row is not None
        assert row.status == REPORT_STATUS_SUCCEEDED
        assert row.status != REPORT_STATUS_PENDING


@pytest.mark.asyncio
async def test_report_run_cycle_isolates_execute_error(pg_engine, pg_session_maker):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Rpt Err Org", domain=f"rpte-{uuid4().hex[:8]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Rpt Err Tenant",
            organization_id=org.id,
            location_code=f"RE-{uuid4().hex[:6]}",
            status=TenantStatus.ACTIVE.value,
        )
        db.add(tenant)
        await db.flush()
        svc = ReportService(db)
        defn = await svc.create_definition(tenant.id, code="wkr_err", name="Worker err")
        await svc.request_run(
            tenant.id, definition_code=defn.code, enqueue_outbox=False
        )
        await db.commit()

    class _Boom:
        def __init__(self, *_a, **_k):
            pass

        async def execute_run(self, *_a, **_k):
            raise RuntimeError("report boom")

    with (
        patch("app.workers.report.AsyncSessionLocal", pg_session_maker),
        patch("app.workers.report.ReportService", _Boom),
    ):
        processed = await run_cycle()
    assert processed == 0
