"""CSRF bootstrap + double-submit for non-exempt unsafe methods.

Uses X-Test-CSRF: enforce so middleware runs even when ENVIRONMENT=test.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.db.session import get_db
from app.main import app
from app.models.organization import Organization
from app.models.rbac import Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User


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


async def _seed_staff(db: AsyncSession, email: str, password: str) -> Tenant:
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash(password),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    org = Organization(
        name=f"CSRF Org {uuid4().hex[:6]}",
        domain=f"csrf-{uuid4().hex[:8]}.test",
    )
    db.add(org)
    await db.flush()
    tenant = Tenant(
        id=uuid4(),
        name="CSRF Tenant",
        organization_id=org.id,
        location_code=f"C-{uuid4().hex[:6]}",
    )
    db.add(tenant)
    await db.flush()
    role = (
        await db.execute(select(Role).where(Role.name == "GYM_OWNER"))
    ).scalar_one_or_none()
    if role is None:
        role = Role(name=f"csrf-role-{uuid4().hex[:8]}", description="csrf")
        db.add(role)
        await db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant.id))
    await db.commit()
    return tenant


@pytest.mark.asyncio
async def test_csrf_bootstrap_returns_token_and_cookie(api_client):
    res = await api_client.get(
        "/api/v1/auth/csrf",
        headers={"X-Test-CSRF": "enforce"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("csrf_token")
    assert "csrf_token" in res.cookies
    assert res.cookies["csrf_token"] == body["csrf_token"]


@pytest.mark.asyncio
async def test_post_members_without_csrf_header_forbidden(api_client, pg_session_maker):
    email = f"csrf-{uuid4().hex[:8]}@example.com"
    password = "CsrfPass99!"
    async with pg_session_maker() as db:
        tenant = await _seed_staff(db, email, password)

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    session = login.cookies.get("session_token")
    assert session

    # Bootstrap cookie but omit header → 403 when CSRF enforced
    boot = await api_client.get(
        "/api/v1/auth/csrf",
        headers={"X-Test-CSRF": "enforce"},
    )
    assert boot.status_code == 200
    csrf = boot.json()["csrf_token"]

    bad = await api_client.post(
        "/api/v1/members",
        json={
            "member_number": "CSRF-001",
            "first_name": "No",
            "last_name": "Header",
        },
        headers={
            "X-Test-CSRF": "enforce",
            "X-Tenant-ID": str(tenant.id),
        },
        cookies={"session_token": session, "csrf_token": csrf},
    )
    assert bad.status_code == 403

    good = await api_client.post(
        "/api/v1/members",
        json={
            "member_number": "CSRF-002",
            "first_name": "With",
            "last_name": "Header",
        },
        headers={
            "X-Test-CSRF": "enforce",
            "X-CSRF-Token": csrf,
            "X-Tenant-ID": str(tenant.id),
        },
        cookies={"session_token": session, "csrf_token": csrf},
    )
    # 200/201 create, or 403/422 if RBAC lacks members:write — must not be CSRF 403
    assert good.status_code != 403 or "CSRF" not in good.text
    # Prefer success when perms allow
    if good.status_code in (200, 201):
        assert good.json().get("member_number") == "CSRF-002"


@pytest.mark.asyncio
async def test_bearer_header_does_not_waive_csrf_when_session_cookie_present(
    api_client, pg_session_maker
):
    """An attacker-supplied Bearer header must not disarm the cookie CSRF check.

    get_session_token_from_cookie prefers the cookie, so a request carrying both
    authenticates ambiently. The Bearer exemption only applies with no cookie.
    """
    email = f"csrf-bearer-{uuid4().hex[:8]}@example.com"
    password = "CsrfPass99!"
    async with pg_session_maker() as db:
        tenant = await _seed_staff(db, email, password)

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    session = login.cookies.get("session_token")
    assert session

    boot = await api_client.get("/api/v1/auth/csrf", headers={"X-Test-CSRF": "enforce"})
    csrf = boot.json()["csrf_token"]

    res = await api_client.post(
        "/api/v1/members",
        json={
            "member_number": "CSRF-BEARER",
            "first_name": "Bearer",
            "last_name": "Bypass",
        },
        headers={
            "X-Test-CSRF": "enforce",
            "Authorization": "Bearer attacker-supplied-value",
            "X-Tenant-ID": str(tenant.id),
        },
        cookies={"session_token": session, "csrf_token": csrf},
    )
    assert res.status_code == 403
    assert "CSRF" in res.text

    # Same call with no session cookie keeps the legitimate Bearer exemption.
    # The client jar still holds the login cookies, so drop them first.
    api_client.cookies.clear()
    exempt = await api_client.post(
        "/api/v1/members",
        json={
            "member_number": "CSRF-BEARER-2",
            "first_name": "Bearer",
            "last_name": "Only",
        },
        headers={
            "X-Test-CSRF": "enforce",
            "Authorization": f"Bearer {session}",
            "X-Tenant-ID": str(tenant.id),
        },
    )
    assert exempt.status_code != 403 or "CSRF" not in exempt.text
