from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.access import AccessAttempt, AccessStatus
from app.models.organization import Organization
from app.models.retention import DataRetentionPolicy, DeletionMethod
from app.models.tenant import Tenant, TenantStatus
from app.workers.retention import run_retention_sweep


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest.mark.asyncio
async def test_retention_worker_sweep(db_session: AsyncSession):
    # 1. Create org, tenant and policy
    org = Organization(name="Retention Org", domain=f"org-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()

    tenant = Tenant(
        id=uuid4(),
        organization_id=org.id,
        name="Retention Worker Gym",
        status=TenantStatus.ACTIVE.value,
        location_code="RET-01",
    )
    db_session.add(tenant)
    await db_session.flush()

    policy = DataRetentionPolicy(
        id=uuid4(),
        tenant_id=tenant.id,
        data_category="access_logs",
        description="Auto delete old scans after 30 days",
        retention_days=30,
        deletion_method=DeletionMethod.DELETE.value,
        is_active=True,
    )
    db_session.add(policy)

    # 2. Add old and fresh access attempts
    old_attempt = AccessAttempt(
        id=uuid4(),
        tenant_id=tenant.id,
        device_id=None,
        member_id=None,
        status=AccessStatus.GRANTED,
        jti="jti-old",
        timestamp=datetime.now(UTC) - timedelta(days=45),
        snapshot_data={"status": "old"},
    )
    new_attempt = AccessAttempt(
        id=uuid4(),
        tenant_id=tenant.id,
        device_id=None,
        member_id=None,
        status=AccessStatus.GRANTED,
        jti="jti-new",
        timestamp=datetime.now(UTC) - timedelta(days=5),
        snapshot_data={"status": "new"},
    )
    db_session.add_all([old_attempt, new_attempt])
    await db_session.commit()

    # 3. Execute worker sweep
    affected = await run_retention_sweep(db_session)
    assert affected >= 1

    # 4. Verify old record was deleted and new record remains
    res = await db_session.execute(
        select(AccessAttempt).where(AccessAttempt.tenant_id == tenant.id)
    )
    remaining = list(res.scalars().all())
    assert len(remaining) == 1
    assert remaining[0].id == new_attempt.id
