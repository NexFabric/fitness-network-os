"""Step-up MFA is required for sensitive writes when TOTP is enrolled."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pyotp
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import encrypt_string
from app.db.session import get_db
from app.main import app
from app.models.organization import Organization
from app.models.rbac import Permission, Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User, UserMfaMethod, UserSession


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


async def _owner_with_totp(pg_engine):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    secret = pyotp.random_base32()
    async with maker() as db:
        org = Organization(name="SU Org", domain=f"su-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="SU T",
            organization_id=org.id,
            location_code=f"SU-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()
        user = User(
            email=f"su-{uuid4().hex[:8]}@example.com",
            hashed_password="x",
            is_active=True,
        )
        db.add(user)
        await db.flush()
        existing = (
            await db.execute(select(Permission).where(Permission.name == "devices:manage"))
        ).scalar_one_or_none()
        if existing is None:
            existing = Permission(name="devices:manage", description="devices")
            db.add(existing)
            await db.flush()
        role = Role(
            name=f"OWN-{uuid4().hex[:8]}",
            description="owner clone",
            permissions=[existing],
        )
        db.add(role)
        await db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant.id))
        raw = f"tok_{uuid4().hex}"
        db.add(
            UserSession(
                user_id=user.id,
                token_hash=hashlib.sha256(raw.encode()).hexdigest(),
                expires_at=datetime.now(UTC) + timedelta(days=1),
                auth_level="full",
            )
        )
        db.add(
            UserMfaMethod(
                user_id=user.id,
                encrypted_secret=encrypt_string(secret),
                provider_id="totp",
                is_active=True,
            )
        )
        await db.commit()
        return tenant.id, raw, secret


@pytest.mark.asyncio
async def test_device_provision_requires_step_up_when_mfa_enrolled(
    api_client, pg_engine
):
    tenant_id, token, secret = await _owner_with_totp(pg_engine)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }
    denied = await api_client.post(
        "/api/v1/devices/provision",
        headers=headers,
        json={"name": "Gate", "location_id": str(uuid4())},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "step_up_required"

    stepped = await api_client.post(
        "/api/v1/auth/mfa/step-up",
        headers=headers,
        json={"code": pyotp.TOTP(secret).now()},
    )
    assert stepped.status_code == 200, stepped.text

    # After step-up the handler proceeds; missing location is a 404, not 403.
    again = await api_client.post(
        "/api/v1/devices/provision",
        headers=headers,
        json={"name": "Gate", "location_id": str(uuid4())},
    )
    assert again.status_code == 404
