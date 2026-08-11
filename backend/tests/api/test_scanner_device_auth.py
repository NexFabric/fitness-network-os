from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import get_db
from app.main import app
from app.models.access import Device, DeviceStatus
from app.models.audit import AuditEvent
from tests.api.test_auth_login import _seed_user


@pytest.fixture
async def api_client(pg_session_maker):
    async def override_get_db():
        async with pg_session_maker() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_device_provisioning_and_auth(api_client, pg_session_maker):
    # 1. Setup admin user and tenant
    email = f"admin-{uuid4().hex[:8]}@example.com"
    password = "AdminPassword1!"
    async with pg_session_maker() as db:
        user, tenant = await _seed_user(db, email=email, password=password)
        # Give user devices:manage permission
        from sqlalchemy.orm import selectinload

        from app.models.rbac import Permission, Role, UserRole
        
        perm = Permission(name="devices:manage", description="Manage devices")
        db.add(perm)
        await db.flush()
        
        # User role is created in _seed_user, let's just find it
        role_row = (await db.execute(select(UserRole).where(UserRole.user_id == user.id))).scalar_one()
        role = (await db.execute(select(Role).options(selectinload(Role.permissions)).where(Role.id == role_row.role_id))).scalar_one()
        role.permissions.append(perm)
        await db.commit()
        
    # Login as admin
    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    admin_cookie = login.cookies["session_token"]
    
    # 2. Provision device
    # Create location first
    async with pg_session_maker() as db:
        from sqlalchemy import text

        from app.models.location import Location
        await db.execute(text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": str(tenant.id)})
        location = Location(tenant_id=tenant.id, name="Test Location")
        db.add(location)
        await db.commit()
        location_id = location.id

    prov_res = await api_client.post(
        "/api/v1/devices/provision",
        headers={"X-Tenant-ID": str(tenant.id)},
        cookies={"session_token": admin_cookie},
        json={"name": "Scanner 1", "location_id": str(location_id)},
    )
    assert prov_res.status_code == 200
    prov_data = prov_res.json()
    device_id = prov_data["id"]
    device_tenant_id = prov_data["tenant_id"]
    api_key = prov_data["api_key"]
    
    # Check audit log for provision
    async with pg_session_maker() as db:
        from sqlalchemy import text
        await db.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(device_tenant_id)})
        audit = (await db.execute(select(AuditEvent).where(AuditEvent.resource_id == device_id))).scalar_one()
        assert audit.action == "device_provisioned"
    
    # 3. Authenticate device
    auth_res = await api_client.post(
        "/api/v1/devices/auth",
        json={"device_id": device_id, "tenant_id": device_tenant_id, "api_key": api_key},
    )
    assert auth_res.status_code == 200
    assert "device_session" in auth_res.cookies
    device_cookie = auth_res.cookies["device_session"]
    
    # Check device is online
    async with pg_session_maker() as db:
        from sqlalchemy import text
        await db.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(device_tenant_id)})
        device = (await db.execute(select(Device).where(Device.id == device_id))).scalar_one()
        assert device.status == DeviceStatus.ONLINE
    
    # 4. Scanner cannot hit staff API
    staff_res = await api_client.get(
        "/api/v1/devices/",
        headers={"X-Tenant-ID": str(tenant.id)},
        cookies={"session_token": device_cookie}, # Passing device cookie as if it was a user session
    )
    # The deps.py expects "session_token" for user. If we pass it, it should fail
    # because the device token hash won't be in `user_sessions`.
    assert staff_res.status_code == 401
    
    # 5. Revoke device
    revoke_res = await api_client.post(
        "/api/v1/devices/revoke",
        headers={"X-Tenant-ID": str(tenant.id)},
        cookies={"session_token": admin_cookie},
        json={"device_id": device_id},
    )
    assert revoke_res.status_code == 200
    
    # Check audit log for revoke
    async with pg_session_maker() as db:
        audit = (await db.execute(select(AuditEvent).where(AuditEvent.resource_id == device_id, AuditEvent.action == "device_revoked"))).scalar_one()
        assert audit.action == "device_revoked"
        
    # 6. Authenticate device should fail now
    auth_res2 = await api_client.post(
        "/api/v1/devices/auth",
        json={"device_id": device_id, "tenant_id": device_tenant_id, "api_key": api_key},
    )
    assert auth_res2.status_code == 401
