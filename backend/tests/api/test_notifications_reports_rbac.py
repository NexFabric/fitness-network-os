"""Phase 16 — MEMBER must not access notification/report staff surfaces (403)."""

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
from app.models.rbac import Permission, Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User, UserSession


def _token_pair() -> tuple[str, str]:
    raw = f"tok_{uuid4().hex}"
    return raw, hashlib.sha256(raw.encode()).hexdigest()


async def _ensure_perms(db: AsyncSession, names: list[str]) -> list[Permission]:
    out: list[Permission] = []
    for name in names:
        row = (
            await db.execute(select(Permission).where(Permission.name == name))
        ).scalar_one_or_none()
        if row is None:
            row = Permission(name=name, description=name)
            db.add(row)
            await db.flush()
        out.append(row)
    return out


async def _user_with_role(
    db: AsyncSession,
    *,
    tenant_id,
    role_name: str,
    perm_names: list[str],
    email_prefix: str,
) -> tuple[User, str]:
    raw, th = _token_pair()
    user = User(
        email=f"{email_prefix}-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    perms = await _ensure_perms(db, perm_names)
    role = Role(
        name=f"{role_name}-{uuid4().hex[:8]}",
        description=f"test clone of {role_name}",
        permissions=perms,
    )
    db.add(role)
    await db.flush()
    db.add(
        UserRole(
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant_id,
        )
    )
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=th,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
    )
    await db.flush()
    return user, raw


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


MEMBER_SELF_PERMS = [
    "profile:read",
    "profile:write",
    "memberships:read:self",
    "checkins:read:self",
    "checkins:write:self",
    "entitlements:read:self",
    "entitlements:check:self",
    "access:issue:self",
]


@pytest.mark.asyncio
async def test_member_forbidden_on_notifications_and_reports(api_client, pg_engine):
    """MEMBER has tenant access but no notifications:/reports: staff perms → 403."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="N16 RBAC Org", domain=f"n16-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="N16 RBAC T",
            organization_id=org.id,
            location_code=f"N16-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()

        _member, token_member = await _user_with_role(
            db,
            tenant_id=tenant.id,
            role_name="MEMBER",
            perm_names=MEMBER_SELF_PERMS,
            email_prefix="mem-n16",
        )
        await db.commit()
        tenant_id = tenant.id

    headers = {
        "Authorization": f"Bearer {token_member}",
        "X-Tenant-ID": str(tenant_id),
    }

    # Notifications staff surfaces
    r_templates = await api_client.get(
        "/api/v1/notifications/templates", headers=headers
    )
    r_create_tmpl = await api_client.post(
        "/api/v1/notifications/templates",
        headers=headers,
        json={
            "code": "x",
            "name": "X",
            "channel": "EMAIL",
            "body_template": "hi",
        },
    )
    r_schedule = await api_client.post(
        "/api/v1/notifications/deliveries",
        headers=headers,
        json={
            "channel": "EMAIL",
            "recipient_address": "a@b.c",
            "body": "hello",
        },
    )
    r_get_delivery = await api_client.get(
        f"/api/v1/notifications/deliveries/{uuid4()}",
        headers=headers,
    )

    # Reports staff surfaces
    r_defs = await api_client.get("/api/v1/reports/definitions", headers=headers)
    r_create_def = await api_client.post(
        "/api/v1/reports/definitions",
        headers=headers,
        json={"code": "rev", "name": "Revenue"},
    )
    r_run = await api_client.post(
        "/api/v1/reports/runs",
        headers=headers,
        json={"definition_code": "rev"},
    )
    r_get_run = await api_client.get(
        f"/api/v1/reports/runs/{uuid4()}",
        headers=headers,
    )

    for name, resp in [
        ("list_templates", r_templates),
        ("create_template", r_create_tmpl),
        ("schedule_delivery", r_schedule),
        ("get_delivery", r_get_delivery),
        ("list_definitions", r_defs),
        ("create_definition", r_create_def),
        ("request_run", r_run),
        ("get_run", r_get_run),
    ]:
        assert resp.status_code == 403, (
            f"{name} expected 403 got {resp.status_code}: {resp.text}"
        )
