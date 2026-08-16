"""Notification worker cycle is callable and commits without looping forever."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.organization import Organization
from app.models.tenant import Tenant, TenantStatus
from app.workers.notification import run_cycle


@pytest.mark.asyncio
async def test_notification_run_cycle_on_empty_queue(pg_session_maker):
    # Use the test sessionmaker; the module-level engine is bound to another loop.
    with patch("app.workers.notification.AsyncSessionLocal", pg_session_maker):
        processed = await run_cycle()
    assert processed == 0


@pytest.mark.asyncio
async def test_notification_run_cycle_visits_active_tenant(pg_engine, pg_session_maker):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Ntf Wkr Org", domain=f"ntfw-{uuid4().hex[:8]}.com")
        db.add(org)
        await db.flush()
        db.add(
            Tenant(
                id=uuid4(),
                name="Ntf Wkr Tenant",
                organization_id=org.id,
                location_code=f"NW-{uuid4().hex[:6]}",
                status=TenantStatus.ACTIVE.value,
            )
        )
        await db.commit()

    with patch("app.workers.notification.AsyncSessionLocal", pg_session_maker):
        processed = await run_cycle()
    assert processed == 0
