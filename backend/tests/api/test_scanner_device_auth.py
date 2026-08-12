import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.device_auth import (
    MAX_CLOCK_SKEW_SECONDS,
    NONCE_HEADER,
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    build_canonical_string,
)
from app.db.session import get_db
from app.main import app
from app.models.access import Device, DeviceStatus
from app.models.audit import AuditEvent
from tests.api.test_auth_login import _seed_user

VALIDATE_PATH = "/api/v1/devices/qr/validate"


def _sign(
    secret: str,
    method: str,
    path: str,
    body: bytes,
    *,
    timestamp: int | None = None,
    nonce: str | None = None,
) -> dict[str, str]:
    """Build the headers a compliant device would send (mirrors the PWA client)."""
    ts = str(timestamp if timestamp is not None else int(datetime.now(UTC).timestamp()))
    nc = nonce or secrets.token_hex(16)
    pad = "=" * (-len(secret) % 4)
    key = base64.urlsafe_b64decode(secret + pad)
    canonical = build_canonical_string(method, path, ts, nc, body)
    sig = hmac.new(key, canonical.encode(), hashlib.sha256).hexdigest()
    return {TIMESTAMP_HEADER: ts, NONCE_HEADER: nc, SIGNATURE_HEADER: sig}


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


async def _seed_admin_and_device(api_client, pg_session_maker):
    """Admin with devices:manage + a provisioned device. Returns the raw pieces."""
    email = f"admin-{uuid4().hex[:8]}@example.com"
    password = "AdminPassword1!"
    async with pg_session_maker() as db:
        user, tenant = await _seed_user(db, email=email, password=password)
        # Give user devices:manage permission
        from sqlalchemy.orm import selectinload

        from app.models.rbac import Permission, Role, UserRole
        
        # devices:manage is seeded by migration r1e2f3a4b5c6, so get-or-create.
        perm = (
            await db.execute(
                select(Permission).where(Permission.name == "devices:manage")
            )
        ).scalar_one_or_none()
        if perm is None:
            perm = Permission(name="devices:manage", description="Manage devices")
            db.add(perm)
            await db.flush()
        
        # User role is created in _seed_user, let's just find it
        role_row = (await db.execute(select(UserRole).where(UserRole.user_id == user.id))).scalar_one()
        role = (await db.execute(select(Role).options(selectinload(Role.permissions)).where(Role.id == role_row.role_id))).scalar_one()
        # The seeded role may already hold it (migration r1e2f3a4b5c6).
        if perm.id not in {p.id for p in role.permissions}:
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
    return {
        "tenant": tenant,
        "admin_cookie": admin_cookie,
        "location_id": location_id,
        "device_id": prov_data["id"],
        "device_tenant_id": prov_data["tenant_id"],
        "api_key": prov_data["api_key"],
    }


@pytest.mark.asyncio
async def test_device_provisioning_and_auth(api_client, pg_session_maker):
    seeded = await _seed_admin_and_device(api_client, pg_session_maker)
    tenant = seeded["tenant"]
    admin_cookie = seeded["admin_cookie"]
    device_id = seeded["device_id"]
    device_tenant_id = seeded["device_tenant_id"]
    api_key = seeded["api_key"]


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

    # The session token is only half the credential: the signing secret is
    # handed out here, in the body, and never travels in a cookie.
    auth_data = auth_res.json()
    assert auth_data["signature_algorithm"] == "HMAC-SHA256"
    assert auth_data["max_clock_skew_seconds"] == MAX_CLOCK_SKEW_SECONDS
    assert len(auth_data["signing_secret"]) >= 32
    assert auth_data["session_id"]
    
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
        from sqlalchemy import text

        # audit_events is RLS-protected (migration t3a4b5c6d7e8): without tenant
        # context this session correctly sees zero rows.
        await db.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant.id)},
        )
        audit = (await db.execute(select(AuditEvent).where(AuditEvent.resource_id == device_id, AuditEvent.action == "device_revoked"))).scalar_one()
        assert audit.action == "device_revoked"
        
    # 6. Authenticate device should fail now
    auth_res2 = await api_client.post(
        "/api/v1/devices/auth",
        json={"device_id": device_id, "tenant_id": device_tenant_id, "api_key": api_key},
    )
    assert auth_res2.status_code == 401


@pytest.mark.asyncio
async def test_device_request_signing_is_enforced(api_client, pg_session_maker):
    """A stolen device_session cookie must not be a usable credential on its own."""
    seeded = await _seed_admin_and_device(api_client, pg_session_maker)

    auth_res = await api_client.post(
        "/api/v1/devices/auth",
        json={
            "device_id": seeded["device_id"],
            "tenant_id": seeded["device_tenant_id"],
            "api_key": seeded["api_key"],
        },
    )
    assert auth_res.status_code == 200
    cookie = auth_res.cookies["device_session"]
    secret = auth_res.json()["signing_secret"]

    payload = {"token": "not-a-real-qr", "action": "GYM_ENTRY", "consume": False}
    body = json.dumps(payload).encode()

    async def post(headers: dict[str, str]):
        return await api_client.post(
            VALIDATE_PATH,
            content=body,
            headers={"Content-Type": "application/json", **headers},
            cookies={"device_session": cookie},
        )

    # 1. Cookie alone — the exact attacker position this closes.
    res = await post({})
    assert res.status_code == 401
    assert res.json()["detail"] == "device_signature_missing"

    # 2. Cookie + a forged signature.
    forged = _sign(secret, "POST", VALIDATE_PATH, body)
    forged[SIGNATURE_HEADER] = "0" * 64
    res = await post(forged)
    assert res.status_code == 401
    assert res.json()["detail"] == "device_signature_invalid"

    # 3. Signature computed over a different body than the one sent.
    mismatched = _sign(secret, "POST", VALIDATE_PATH, b'{"token":"other"}')
    res = await post(mismatched)
    assert res.status_code == 401
    assert res.json()["detail"] == "device_signature_invalid"

    # 4. Correctly signed but stale — outside the accepted clock skew.
    stale = _sign(
        secret,
        "POST",
        VALIDATE_PATH,
        body,
        timestamp=int(datetime.now(UTC).timestamp()) - (MAX_CLOCK_SKEW_SECONDS + 60),
    )
    res = await post(stale)
    assert res.status_code == 401
    assert res.json()["detail"] == "device_timestamp_skew"

    # 5. Properly signed: authentication passes. The QR itself is junk, so the
    #    access decision denies (403) — that is the layer below, and reaching it
    #    is exactly what proves the device was authenticated.
    good = _sign(secret, "POST", VALIDATE_PATH, body)
    res = await post(good)
    assert res.status_code != 401

    # 6. Capturing that same signed request and sending it again is refused.
    replayed = await post(good)
    assert replayed.status_code == 401
    assert replayed.json()["detail"] == "device_nonce_replay"


@pytest.mark.asyncio
async def test_device_session_without_signing_material_is_rejected(
    api_client, pg_session_maker
):
    """Sessions issued before request signing fail closed instead of falling back."""
    from sqlalchemy import text, update

    from app.models.access import DeviceSession

    seeded = await _seed_admin_and_device(api_client, pg_session_maker)
    auth_res = await api_client.post(
        "/api/v1/devices/auth",
        json={
            "device_id": seeded["device_id"],
            "tenant_id": seeded["device_tenant_id"],
            "api_key": seeded["api_key"],
        },
    )
    cookie = auth_res.cookies["device_session"]
    secret = auth_res.json()["signing_secret"]
    session_id = auth_res.json()["session_id"]

    async with pg_session_maker() as db:
        await db.execute(
            text("SELECT set_config('app.current_tenant_id', :t, true)"),
            {"t": str(seeded["device_tenant_id"])},
        )
        await db.execute(
            update(DeviceSession)
            .where(DeviceSession.id == session_id)
            .values(signing_key_material=None)
        )
        await db.commit()

    payload = {"token": "not-a-real-qr", "action": "GYM_ENTRY", "consume": False}
    body = json.dumps(payload).encode()
    res = await api_client.post(
        VALIDATE_PATH,
        content=body,
        headers={
            "Content-Type": "application/json",
            **_sign(secret, "POST", VALIDATE_PATH, body),
        },
        cookies={"device_session": cookie},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "device_session_unsigned"
