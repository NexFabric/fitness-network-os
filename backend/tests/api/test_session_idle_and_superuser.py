"""Idle timeout and platform-superuser write gates."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import get_db
from app.main import app
from app.models.organization import Organization
from app.models.rbac import Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User, UserSession


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


async def _privileged_session(
    pg_engine, *, last_seen_at: datetime | None, role_name: str = "GYM_OWNER"
) -> tuple[object, str]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    raw = f"tok_{uuid4().hex}"
    async with maker() as db:
        org = Organization(name="Idle Org", domain=f"idle-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Idle T",
            organization_id=org.id,
            location_code=f"ID-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()
        user = User(
            email=f"idle-{uuid4().hex[:8]}@example.com",
            hashed_password="x",
            is_active=True,
        )
        db.add(user)
        await db.flush()
        role = (
            await db.execute(select(Role).where(Role.name == role_name))
        ).scalar_one_or_none()
        if role is None:
            role = Role(name=role_name, description=role_name, is_system=True)
            db.add(role)
            await db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant.id))
        db.add(
            UserSession(
                user_id=user.id,
                token_hash=hashlib.sha256(raw.encode()).hexdigest(),
                expires_at=datetime.now(UTC) + timedelta(days=1),
                auth_level="full",
                last_seen_at=last_seen_at,
            )
        )
        await db.commit()
        return tenant.id, raw


@pytest.mark.asyncio
async def test_privileged_session_revoked_after_idle_window(api_client, pg_engine):
    stale = datetime.now(UTC) - timedelta(minutes=31)
    tenant_id, token = await _privileged_session(pg_engine, last_seen_at=stale)
    res = await api_client.get(
        "/api/v1/me/session",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant_id),
        },
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "session_idle"


@pytest.mark.asyncio
async def test_privileged_session_stays_alive_within_idle_window(api_client, pg_engine):
    recent = datetime.now(UTC) - timedelta(minutes=5)
    tenant_id, token = await _privileged_session(pg_engine, last_seen_at=recent)
    res = await api_client.get(
        "/api/v1/me/session",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant_id),
        },
    )
    assert res.status_code == 200, res.text


@pytest.mark.asyncio
async def test_superuser_cannot_create_tenant_without_break_glass(
    api_client, pg_engine
):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    raw = f"tok_{uuid4().hex}"
    async with maker() as db:
        org = Organization(name="SU Org", domain=f"su-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        user = User(
            email=f"su-{uuid4().hex[:8]}@example.com",
            hashed_password="x",
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        await db.flush()
        db.add(
            UserSession(
                user_id=user.id,
                token_hash=hashlib.sha256(raw.encode()).hexdigest(),
                expires_at=datetime.now(UTC) + timedelta(days=1),
                auth_level="full",
            )
        )
        await db.commit()
        org_id = org.id

    res = await api_client.post(
        "/api/v1/admin/tenants",
        headers={"Authorization": f"Bearer {raw}"},
        json={
            "organization_id": str(org_id),
            "name": "Yetkisiz Kulüp",
            "location_code": f"XX-{uuid4().hex[:4].upper()}",
        },
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "break_glass_required"
