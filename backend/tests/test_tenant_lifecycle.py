import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.organization import Organization
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def organization(db_session: AsyncSession) -> Organization:
    org = Organization(name="Lifecycle Org", domain=f"org-{uuid.uuid4()}.com")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"user-{uuid.uuid4()}@test.com",
        hashed_password="hash",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.mark.asyncio
async def test_tenant_lifecycle_model(
    db_session: AsyncSession, organization: Organization
):
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Lifecycle Gym",
        organization_id=organization.id,
        location_code="LC-TEST-1",
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)

    # Defaults to ACTIVE
    assert tenant.status == TenantStatus.ACTIVE.value

    # Update to SUSPENDED
    tenant.status = TenantStatus.SUSPENDED.value
    tenant.suspended_at = datetime.now(UTC)
    tenant.suspension_reason = "Billing failure"
    await db_session.commit()

    # Update to CLOSED
    tenant.status = TenantStatus.CLOSED.value
    tenant.closed_at = datetime.now(UTC)
    tenant.closure_reason = "Manual closure"
    await db_session.commit()

    assert tenant.status == TenantStatus.CLOSED.value


@pytest.mark.asyncio
async def test_tenant_status_auth_enforcement(db_session, user, organization):
    # This simulates get_tenant_id enforcement.
    from app.api.deps import get_tenant_id
    from app.models.rbac import Role, UserRole
    from app.models.tenant import Tenant, TenantStatus

    tenant_id = uuid.uuid4()
    tenant = Tenant(
        id=tenant_id,
        name="Auth Test Gym",
        organization_id=organization.id,
        location_code="LC-TEST-AUTH",
        status=TenantStatus.ACTIVE.value,
    )
    db_session.add(tenant)

    role = Role(id=uuid.uuid4(), name="ADMIN")
    db_session.add(role)
    db_session.add(UserRole(user_id=user.id, tenant_id=tenant_id, role_id=role.id))
    await db_session.commit()

    # ACTIVE should not raise
    resolved_id = await get_tenant_id(
        x_tenant_id=str(tenant_id), user=user, db=db_session
    )
    assert resolved_id == tenant_id

    # SUSPENDED should raise 403
    tenant.status = TenantStatus.SUSPENDED.value
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await get_tenant_id(x_tenant_id=str(tenant_id), user=user, db=db_session)
    assert exc.value.status_code == 403
    assert "suspended" in exc.value.detail.lower()

    # CLOSED should raise 403
    tenant.status = TenantStatus.CLOSED.value
    await db_session.commit()

    with pytest.raises(HTTPException) as exc2:
        await get_tenant_id(x_tenant_id=str(tenant_id), user=user, db=db_session)
    assert exc2.value.status_code == 403
    assert "closed" in exc2.value.detail.lower()


@pytest.mark.asyncio
async def test_suspended_tenant_device_auth_is_rejected(db_session, organization):
    import hashlib
    from datetime import timedelta

    from starlette.requests import Request

    from app.api.deps import get_current_device
    from app.models.access import Device, DeviceSession, DeviceStatus
    from app.models.location import Location

    tenant = Tenant(
        id=uuid.uuid4(),
        name="Device Lifecycle Gym",
        organization_id=organization.id,
        location_code=f"DLC-{uuid.uuid4().hex[:6]}",
        status=TenantStatus.ACTIVE.value,
    )
    db_session.add(tenant)
    await db_session.flush()

    loc = Location(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="Turnstile Branch",
    )
    db_session.add(loc)
    await db_session.flush()

    device = Device(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        location_id=loc.id,
        name="Turnstile 1",
        is_active=True,
        status=DeviceStatus.ONLINE,
    )
    db_session.add(device)
    await db_session.flush()

    raw_token = f"dev-token-{uuid.uuid4().hex}"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    session = DeviceSession(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        device_id=device.id,
        token_hash=token_hash,
        signing_key_material="0" * 64,
        is_revoked=False,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    db_session.add(session)
    await db_session.commit()

    # Create dummy mock request
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/access/qr/validate",
        "headers": [(b"authorization", f"Bearer {raw_token}".encode())],
    }
    request = Request(scope)

    # 1. When tenant is SUSPENDED -> get_current_device raises 403
    tenant.status = TenantStatus.SUSPENDED.value
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await get_current_device(request, db=db_session)
    assert exc.value.status_code == 403
    assert "suspended" in exc.value.detail.lower()

    # 2. When tenant is CLOSED -> get_current_device raises 403
    tenant.status = TenantStatus.CLOSED.value
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_closed:
        await get_current_device(request, db=db_session)
    assert exc_closed.value.status_code == 403
    assert "closed" in exc_closed.value.detail.lower()
