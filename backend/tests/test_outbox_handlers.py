from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.event_types import (
    REPORT_RUN_REQUESTED_V1,
)
from app.models.organization import Organization
from app.models.outbox import OutboxEvent
from app.models.tenant import Tenant, TenantStatus
from app.workers.outbox import domain_event_publisher


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest.mark.asyncio
async def test_domain_event_publisher_routes_notification(db_session: AsyncSession):
    org = Organization(name="Outbox Org", domain=f"org-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()

    tenant = Tenant(
        id=uuid4(),
        organization_id=org.id,
        name="Outbox Handler Gym",
        status=TenantStatus.ACTIVE.value,
        location_code="OBX-01",
    )
    db_session.add(tenant)
    await db_session.flush()

    from sqlalchemy import select

    from app.services.notification import NotificationService

    notif_svc = NotificationService(db_session)
    res = await notif_svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_address="user@test.local",
        template_code=None,
        subject="Welcome",
        body="Hello Test",
    )
    assert res.outbox_event_id is not None
    ev_result = await db_session.execute(
        select(OutboxEvent).where(OutboxEvent.id == res.outbox_event_id)
    )
    event = ev_result.scalars().one()

    # Dispatch via domain_event_publisher
    await domain_event_publisher(db_session, event)


@pytest.mark.asyncio
async def test_domain_event_publisher_routes_report(db_session: AsyncSession):
    org = Organization(name="Outbox Report Org", domain=f"org-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()

    tenant = Tenant(
        id=uuid4(),
        organization_id=org.id,
        name="Outbox Report Gym",
        status=TenantStatus.ACTIVE.value,
        location_code="OBR-01",
    )
    db_session.add(tenant)
    await db_session.flush()

    from sqlalchemy import select

    from app.services.report import ReportService

    report_svc = ReportService(db_session)
    await report_svc.create_definition(
        tenant.id,
        code="test_report",
        name="Test Report",
        report_type="REVENUE",
        config={},
    )
    res = await report_svc.request_run(tenant.id, definition_code="test_report")
    assert res.run is not None

    ev_result = await db_session.execute(
        select(OutboxEvent).where(
            OutboxEvent.tenant_id == tenant.id,
            OutboxEvent.event_type == REPORT_RUN_REQUESTED_V1,
        )
    )
    event = ev_result.scalars().first()
    assert event is not None

    # Dispatch via domain_event_publisher
    await domain_event_publisher(db_session, event)


@pytest.mark.asyncio
async def test_domain_event_publisher_routes_domain_event(db_session: AsyncSession):
    org = Organization(name="Outbox Domain Org", domain=f"org-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()

    tenant = Tenant(
        id=uuid4(),
        organization_id=org.id,
        name="Outbox Domain Gym",
        status=TenantStatus.ACTIVE.value,
        location_code="OBD-01",
    )
    db_session.add(tenant)
    await db_session.flush()

    general_event = OutboxEvent(
        id=uuid4(),
        tenant_id=tenant.id,
        event_type="membership.activated.v1",
        aggregate_type="membership",
        aggregate_id=uuid4(),
        payload={"membership_id": str(uuid4())},
        status="PENDING",
        created_at=datetime.now(UTC),
    )
    db_session.add(general_event)
    await db_session.flush()

    # Dispatch via domain_event_publisher
    await domain_event_publisher(db_session, general_event)
