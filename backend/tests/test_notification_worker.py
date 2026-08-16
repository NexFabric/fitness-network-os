"""Notification worker cycle is callable and commits without looping forever."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.organization import Organization
from app.models.tenant import Tenant, TenantStatus
from app.workers.notification import run_cycle


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest.mark.asyncio
async def test_notification_run_cycle_on_empty_queue(db_session: AsyncSession):
    org = Organization(name="Notify Org", domain=f"n-{uuid4().hex[:8]}.com")
    db_session.add(org)
    await db_session.flush()
    db_session.add(
        Tenant(
            id=uuid4(),
            organization_id=org.id,
            name="Notify Gym",
            status=TenantStatus.ACTIVE.value,
            location_code=f"NT-{uuid4().hex[:4]}",
        )
    )
    await db_session.commit()

    processed = await run_cycle()
    assert processed == 0
