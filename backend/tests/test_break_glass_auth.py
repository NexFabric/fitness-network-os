from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_tenant_id
from app.models.organization import Organization
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.services.break_glass import BreakGlassService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest.mark.asyncio
async def test_superuser_without_break_glass_is_forbidden(db_session: AsyncSession):
    # 1. Setup tenant and superuser without UserRole
    org = Organization(name="Foreign Org", domain=f"org-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()

    tenant = Tenant(
        id=uuid4(),
        organization_id=org.id,
        name="Foreign Gym",
        status=TenantStatus.ACTIVE.value,
        location_code="FRG-01",
    )
    db_session.add(tenant)

    superuser = User(
        id=uuid4(),
        email=f"platform_admin_{uuid4()}@nex.local",
        hashed_password="hashed_pass_mock",
        is_superuser=True,
    )
    db_session.add(superuser)
    await db_session.flush()

    # 2. Attempting to get tenant_id without active break-glass should raise 403
    with pytest.raises(HTTPException) as exc_info:
        await get_tenant_id(
            x_tenant_id=str(tenant.id),
            user=superuser,
            db=db_session,
        )

    assert exc_info.value.status_code == 403
    assert "acil durum (break-glass)" in exc_info.value.detail


@pytest.mark.asyncio
async def test_superuser_with_active_break_glass_succeeds(db_session: AsyncSession):
    # 1. Setup tenant and superuser
    org = Organization(name="Emergency Org", domain=f"org-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()

    tenant = Tenant(
        id=uuid4(),
        organization_id=org.id,
        name="Emergency Gym",
        status=TenantStatus.ACTIVE.value,
        location_code="EMG-01",
    )
    db_session.add(tenant)

    superuser = User(
        id=uuid4(),
        email=f"super_ops_{uuid4()}@nex.local",
        hashed_password="hashed_pass_mock",
        is_superuser=True,
    )
    db_session.add(superuser)
    await db_session.flush()

    # 2. Grant active break-glass session
    bg_service = BreakGlassService(db_session)
    await bg_service.create_session(
        actor_id=superuser.id,
        target_tenant_id=tenant.id,
        reason="Prod incident emergency investigation",
        ticket_reference="INC-9911",
        duration_minutes=15,
    )

    # 3. get_tenant_id should now succeed
    resolved_id = await get_tenant_id(
        x_tenant_id=str(tenant.id),
        user=superuser,
        db=db_session,
    )
    assert resolved_id == tenant.id
