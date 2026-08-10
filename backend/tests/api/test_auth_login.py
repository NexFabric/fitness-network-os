"""Auth login/logout API — real Postgres sessions (argon2 + hashed tokens)."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
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


async def _seed_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    with_tenant: bool = True,
    active: bool = True,
) -> tuple[User, Tenant | None]:
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash(password),
        is_active=active,
    )
    db.add(user)
    await db.flush()

    tenant: Tenant | None = None
    if with_tenant:
        org = Organization(
            name=f"Auth Org {uuid4().hex[:6]}",
            domain=f"auth-{uuid4().hex[:8]}.test",
        )
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Auth Tenant",
            organization_id=org.id,
            location_code=f"A-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()

        role = (
            await db.execute(select(Role).where(Role.name == "GYM_OWNER"))
        ).scalar_one_or_none()
        if role is None:
            role = Role(name=f"auth-role-{uuid4().hex[:8]}", description="auth test")
            db.add(role)
            await db.flush()

        db.add(
            UserRole(
                user_id=user.id,
                role_id=role.id,
                tenant_id=tenant.id,
            )
        )
        await db.flush()

    await db.commit()
    return user, tenant


@pytest.mark.asyncio
async def test_login_success_returns_token_and_creates_session(
    api_client, pg_session_maker
):
    email = f"login-{uuid4().hex[:8]}@example.com"
    password = "CorrectHorseBattery1!"
    async with pg_session_maker() as db:
        user, tenant = await _seed_user(db, email=email, password=password)

    res = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert "token" not in body  # token removed from JSON
    assert body["user_id"] == str(user.id)
    assert body["expires_at"]
    assert body["tenant_id"] == str(tenant.id)
    assert "session_token" in res.cookies
    token = res.cookies["session_token"]

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    async with pg_session_maker() as db:
        row = (
            await db.execute(
                select(UserSession).where(UserSession.token_hash == token_hash)
            )
        ).scalar_one()
        assert row.user_id == user.id
        assert row.is_revoked is False
        assert row.expires_at > datetime.now(UTC)


@pytest.mark.asyncio
async def test_login_email_case_normalized(api_client, pg_session_maker):
    email = f"CaseMix-{uuid4().hex[:8]}@Example.COM"
    password = "PwSecret99!"
    async with pg_session_maker() as db:
        await _seed_user(db, email=email.lower(), password=password)

    res = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email.upper(), "password": password},
    )
    assert res.status_code == 200, res.text
    assert "session_token" in res.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(api_client, pg_session_maker):
    email = f"badpw-{uuid4().hex[:8]}@example.com"
    async with pg_session_maker() as db:
        await _seed_user(db, email=email, password="RightPassword1!")

    res = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword1!"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_unknown_email(api_client):
    res = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_logout_revokes_session(api_client, pg_session_maker):
    email = f"logout-{uuid4().hex[:8]}@example.com"
    password = "LogoutPass1!"
    async with pg_session_maker() as db:
        user, _tenant = await _seed_user(db, email=email, password=password)

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    token = login.cookies["session_token"]

    out = await api_client.post(
        "/api/v1/auth/logout",
        cookies={"session_token": token},
    )
    assert out.status_code == 200
    assert out.json()["ok"] is True

    async with pg_session_maker() as db:
        active = (
            await db.execute(
                select(UserSession).where(
                    UserSession.user_id == user.id,
                    UserSession.is_revoked.is_(False),
                )
            )
        ).scalars().all()
        assert active == []

    again = await api_client.post(
        "/api/v1/auth/logout",
        cookies={"session_token": token},
    )
    assert again.status_code == 401


@pytest.mark.asyncio
async def test_login_mfa_required(api_client, pg_session_maker):
    email = f"mfareq-{uuid4().hex[:8]}@example.com"
    password = "MfaPassword1!"
    async with pg_session_maker() as db:
        user, _ = await _seed_user(db, email=email, password=password)
        db.add(UserMfaMethod(user_id=user.id, provider_id="secret123", is_active=True))
        await db.commit()

    res = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "mfa_required"


@pytest.mark.asyncio
async def test_login_mfa_invalid(api_client, pg_session_maker):
    email = f"mfainv-{uuid4().hex[:8]}@example.com"
    password = "MfaPassword1!"
    async with pg_session_maker() as db:
        user, _ = await _seed_user(db, email=email, password=password)
        db.add(UserMfaMethod(user_id=user.id, provider_id="secret123", is_active=True))
        await db.commit()

    res = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "mfa_code": "wrong_code"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "mfa_invalid"


@pytest.mark.asyncio
async def test_login_mfa_success(api_client, pg_session_maker):
    email = f"mfasucc-{uuid4().hex[:8]}@example.com"
    password = "MfaPassword1!"
    async with pg_session_maker() as db:
        user, _ = await _seed_user(db, email=email, password=password)
        db.add(UserMfaMethod(user_id=user.id, provider_id="secret123", is_active=True))
        await db.commit()

    res = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "mfa_code": "secret123"},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_login_mfa_misconfigured(api_client, pg_session_maker):
    email = f"mfamisc-{uuid4().hex[:8]}@example.com"
    password = "MfaPassword1!"
    async with pg_session_maker() as db:
        user, _ = await _seed_user(db, email=email, password=password)
        # Active MFA method registered but provider_id is None/empty
        db.add(UserMfaMethod(user_id=user.id, provider_id="", is_active=True))
        await db.commit()

    res = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "mfa_code": "some_code"},
    )
    assert res.status_code == 500
    assert res.json()["detail"] == "mfa_misconfigured"

