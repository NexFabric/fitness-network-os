"""Phase 16 R-002 — cross-tenant isolation for notifications + reports (service layer).

Proves tenants cannot read each other's notification templates/deliveries or
report definitions/runs via NotificationService / ReportService tenant_id filters.
Optional app_user + app.current_tenant_id RLS check mirrors other RLS suites.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.notification import NotificationDelivery, NotificationTemplate
from app.models.organization import Organization
from app.models.report import ReportDefinition, ReportRun
from app.models.tenant import Tenant
from app.services.notification import NotificationService
from app.services.report import ReportService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        try:
            yield session
        finally:
            await session.rollback()


async def _make_tenant(db: AsyncSession, *, label: str) -> Tenant:
    org = Organization(
        name=f"{label} Org", domain=f"{label.lower()}-{uuid4().hex[:8]}.com"
    )
    db.add(org)
    await db.flush()
    t = Tenant(
        id=uuid4(),
        name=f"{label} Tenant",
        organization_id=org.id,
        location_code=f"{label[:3].upper()}-{uuid4().hex[:6]}",
    )
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
async def tenants_ab(db_session: AsyncSession) -> tuple[Tenant, Tenant]:
    a = await _make_tenant(db_session, label="IsoA")
    b = await _make_tenant(db_session, label="IsoB")
    await db_session.commit()
    return a, b


# ---------------------------------------------------------------------------
# Notification templates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_notification_templates_cross_tenant_get_list_isolated(
    db_session: AsyncSession, tenants_ab: tuple[Tenant, Tenant]
):
    tenant_a, tenant_b = tenants_ab
    svc = NotificationService(db_session)

    tmpl_a = await svc.create_template(
        tenant_a.id,
        code="welcome",
        name="A Welcome",
        channel="EMAIL",
        body_template="Hello A $name",
    )
    tmpl_b = await svc.create_template(
        tenant_b.id,
        code="welcome",
        name="B Welcome",
        channel="EMAIL",
        body_template="Hello B $name",
    )
    await db_session.commit()

    # Same code is per-tenant; A must not resolve B's template row by tenant filter
    as_a = await svc.get_template_by_code(tenant_a.id, "welcome")
    as_b = await svc.get_template_by_code(tenant_b.id, "welcome")
    assert as_a is not None and as_a.id == tmpl_a.id
    assert as_b is not None and as_b.id == tmpl_b.id
    assert as_a.id != as_b.id

    # list_templates scoped to caller tenant only
    list_a = await svc.list_templates(tenant_a.id)
    list_b = await svc.list_templates(tenant_b.id)
    assert {t.id for t in list_a} == {tmpl_a.id}
    assert {t.id for t in list_b} == {tmpl_b.id}
    assert all(t.tenant_id == tenant_a.id for t in list_a)
    assert all(t.tenant_id == tenant_b.id for t in list_b)

    # Unknown code on A when only B has a different code
    await svc.create_template(
        tenant_b.id,
        code="b_only",
        name="B Only",
        channel="SMS",
        body_template="B only",
    )
    await db_session.commit()
    assert await svc.get_template_by_code(tenant_a.id, "b_only") is None
    assert await svc.get_template_by_code(tenant_b.id, "b_only") is not None


# ---------------------------------------------------------------------------
# Notification deliveries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_notification_deliveries_cross_tenant_invisible(
    db_session: AsyncSession, tenants_ab: tuple[Tenant, Tenant]
):
    """Deliveries created for B are not dispatchable/readable under tenant A."""
    tenant_a, tenant_b = tenants_ab
    svc = NotificationService(db_session)

    await svc.create_template(
        tenant_a.id,
        code="ping",
        name="A Ping",
        channel="EMAIL",
        body_template="ping A",
    )
    await svc.create_template(
        tenant_b.id,
        code="ping",
        name="B Ping",
        channel="EMAIL",
        body_template="ping B",
    )
    await db_session.commit()

    sched_a = await svc.schedule_delivery(
        tenant_a.id,
        channel="EMAIL",
        recipient_address="a@example.com",
        template_code="ping",
        enqueue_outbox=False,
    )
    sched_b = await svc.schedule_delivery(
        tenant_b.id,
        channel="EMAIL",
        recipient_address="b@example.com",
        template_code="ping",
        enqueue_outbox=False,
    )
    await db_session.commit()
    delivery_a = sched_a.delivery
    delivery_b = sched_b.delivery
    assert delivery_a.tenant_id == tenant_a.id
    assert delivery_b.tenant_id == tenant_b.id

    # Service-layer tenant filter: dispatch with wrong tenant → not found
    with pytest.raises(ValueError, match="delivery_not_found"):
        await svc.dispatch_delivery(tenant_a.id, delivery_b.id)

    with pytest.raises(ValueError, match="delivery_not_found"):
        await svc.dispatch_delivery(tenant_b.id, delivery_a.id)

    # Explicit get-by-id pattern used by HTTP layer (tenant_id + id)
    row_as_a = (
        (
            await db_session.execute(
                select(NotificationDelivery).where(
                    NotificationDelivery.tenant_id == tenant_a.id,
                    NotificationDelivery.id == delivery_b.id,
                )
            )
        )
        .scalars()
        .first()
    )
    assert row_as_a is None

    row_b_as_b = (
        (
            await db_session.execute(
                select(NotificationDelivery).where(
                    NotificationDelivery.tenant_id == tenant_b.id,
                    NotificationDelivery.id == delivery_b.id,
                )
            )
        )
        .scalars()
        .first()
    )
    assert row_b_as_b is not None and row_b_as_b.id == delivery_b.id

    # process_due_failed is tenant-scoped — B's FAILED delivery is not claimed as A
    delivery_b.status = "FAILED"
    delivery_b.available_at = None
    await db_session.flush()
    counts_a = await svc.process_due_failed(tenant_a.id, limit=50)
    assert counts_a == {"sent": 0, "failed": 0, "dead": 0}
    # B's row still FAILED (not dispatched under A)
    await db_session.refresh(delivery_b)
    assert delivery_b.status == "FAILED"


# ---------------------------------------------------------------------------
# Report definitions + runs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_report_definitions_cross_tenant_get_list_isolated(
    db_session: AsyncSession, tenants_ab: tuple[Tenant, Tenant]
):
    tenant_a, tenant_b = tenants_ab
    svc = ReportService(db_session)

    def_a = await svc.create_definition(
        tenant_a.id,
        code="monthly_revenue",
        name="A Revenue",
        report_type="REVENUE",
    )
    def_b = await svc.create_definition(
        tenant_b.id,
        code="monthly_revenue",
        name="B Revenue",
        report_type="REVENUE",
    )
    await db_session.commit()

    as_a = await svc.get_definition_by_code(tenant_a.id, "monthly_revenue")
    as_b = await svc.get_definition_by_code(tenant_b.id, "monthly_revenue")
    assert as_a is not None and as_a.id == def_a.id
    assert as_b is not None and as_b.id == def_b.id
    assert as_a.id != as_b.id

    list_a = await svc.list_definitions(tenant_a.id)
    list_b = await svc.list_definitions(tenant_b.id)
    assert {d.id for d in list_a} == {def_a.id}
    assert {d.id for d in list_b} == {def_b.id}

    await svc.create_definition(tenant_b.id, code="b_only_report", name="B Only Report")
    await db_session.commit()
    assert await svc.get_definition_by_code(tenant_a.id, "b_only_report") is None
    assert await svc.get_definition_by_code(tenant_b.id, "b_only_report") is not None


@pytest.mark.asyncio
async def test_report_runs_cross_tenant_get_execute_isolated(
    db_session: AsyncSession, tenants_ab: tuple[Tenant, Tenant]
):
    tenant_a, tenant_b = tenants_ab
    svc = ReportService(db_session)

    await svc.create_definition(tenant_a.id, code="export", name="A Export")
    await svc.create_definition(tenant_b.id, code="export", name="B Export")
    await db_session.commit()

    run_a = (
        await svc.request_run(
            tenant_a.id, definition_code="export", enqueue_outbox=False
        )
    ).run
    run_b = (
        await svc.request_run(
            tenant_b.id, definition_code="export", enqueue_outbox=False
        )
    ).run
    await db_session.commit()

    # get_run with wrong tenant → None
    assert await svc.get_run(tenant_a.id, run_b.id) is None
    assert await svc.get_run(tenant_b.id, run_a.id) is None
    assert (await svc.get_run(tenant_a.id, run_a.id)).id == run_a.id
    assert (await svc.get_run(tenant_b.id, run_b.id)).id == run_b.id

    # execute_run with wrong tenant → run_not_found
    with pytest.raises(ValueError, match="run_not_found"):
        await svc.execute_run(tenant_a.id, run_b.id)
    with pytest.raises(ValueError, match="run_not_found"):
        await svc.execute_run(tenant_b.id, run_a.id)

    # Own tenant can execute
    executed = await svc.execute_run(tenant_a.id, run_a.id)
    await db_session.commit()
    assert executed.status == "SUCCEEDED"


# ---------------------------------------------------------------------------
# Optional: app_user session + GUC RLS (when easy via pg_session_maker)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_phase16_tables_rls_app_user_guc(
    db_session: AsyncSession,
    tenants_ab: tuple[Tenant, Tenant],
    pg_session_maker,
):
    """app_user with SET LOCAL app.current_tenant_id must not see peer tenant rows."""
    tenant_a, tenant_b = tenants_ab
    notif = NotificationService(db_session)
    report = ReportService(db_session)

    tmpl_a = await notif.create_template(
        tenant_a.id,
        code="rls_a",
        name="RLS A",
        channel="EMAIL",
        body_template="a",
    )
    tmpl_b = await notif.create_template(
        tenant_b.id,
        code="rls_b",
        name="RLS B",
        channel="EMAIL",
        body_template="b",
    )
    del_a = (
        await notif.schedule_delivery(
            tenant_a.id,
            channel="EMAIL",
            recipient_address="a@ex.com",
            body="a body",
            enqueue_outbox=False,
        )
    ).delivery
    del_b = (
        await notif.schedule_delivery(
            tenant_b.id,
            channel="EMAIL",
            recipient_address="b@ex.com",
            body="b body",
            enqueue_outbox=False,
        )
    ).delivery
    def_a = await report.create_definition(
        tenant_a.id, code="rls_def_a", name="RLS Def A"
    )
    def_b = await report.create_definition(
        tenant_b.id, code="rls_def_b", name="RLS Def B"
    )
    run_a = (
        await report.request_run(
            tenant_a.id, definition_code="rls_def_a", enqueue_outbox=False
        )
    ).run
    run_b = (
        await report.request_run(
            tenant_b.id, definition_code="rls_def_b", enqueue_outbox=False
        )
    ).run
    await db_session.commit()

    async with pg_session_maker() as session:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant_a.id)},
        )

        templates = (
            (await session.execute(select(NotificationTemplate))).scalars().all()
        )
        assert all(t.tenant_id == tenant_a.id for t in templates)
        assert any(t.id == tmpl_a.id for t in templates)
        assert all(t.id != tmpl_b.id for t in templates)

        deliveries = (
            (await session.execute(select(NotificationDelivery))).scalars().all()
        )
        assert all(d.tenant_id == tenant_a.id for d in deliveries)
        assert any(d.id == del_a.id for d in deliveries)
        assert all(d.id != del_b.id for d in deliveries)

        definitions = (await session.execute(select(ReportDefinition))).scalars().all()
        assert all(d.tenant_id == tenant_a.id for d in definitions)
        assert any(d.id == def_a.id for d in definitions)
        assert all(d.id != def_b.id for d in definitions)

        runs = (await session.execute(select(ReportRun))).scalars().all()
        assert all(r.tenant_id == tenant_a.id for r in runs)
        assert any(r.id == run_a.id for r in runs)
        assert all(r.id != run_b.id for r in runs)
