"""Auth login/logout API — real Postgres sessions (argon2 + hashed tokens)."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import uuid4

import pyotp
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_string, get_password_hash
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
    role_name: str = "AUTH_TEST_STAFF",
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
            await db.execute(select(Role).where(Role.name == role_name))
        ).scalar_one_or_none()
        if role is None:
            role = Role(name=role_name, description="auth test")
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
            (
                await db.execute(
                    select(UserSession).where(
                        UserSession.user_id == user.id,
                        UserSession.is_revoked.is_(False),
                    )
                )
            )
            .scalars()
            .all()
        )
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
        db.add(
            UserMfaMethod(
                user_id=user.id,
                encrypted_secret=encrypt_string(pyotp.random_base32()),
                provider_id="totp",
                is_active=True,
            )
        )
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
        db.add(
            UserMfaMethod(
                user_id=user.id,
                encrypted_secret=encrypt_string(pyotp.random_base32()),
                provider_id="totp",
                is_active=True,
            )
        )
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
    totp_secret = pyotp.random_base32()
    async with pg_session_maker() as db:
        user, _ = await _seed_user(db, email=email, password=password)
        db.add(
            UserMfaMethod(
                user_id=user.id,
                encrypted_secret=encrypt_string(totp_secret),
                provider_id="totp",
                is_active=True,
            )
        )
        await db.commit()

    totp = pyotp.TOTP(totp_secret)
    res = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "mfa_code": totp.now()},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_privileged_login_without_enrollment_gets_restricted_session(
    api_client, pg_session_maker
):
    email = f"mfa-enroll-{uuid4().hex[:8]}@example.com"
    password = "MfaPassword1!"
    async with pg_session_maker() as db:
        user, tenant = await _seed_user(
            db,
            email=email,
            password=password,
            role_name="GYM_OWNER",
        )

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    assert login.json()["mfa_enrollment_required"] is True
    assert login.json()["tenant_id"] == str(tenant.id)
    token = login.cookies["session_token"]

    denied = await api_client.get(
        "/api/v1/me/session",
        cookies={"session_token": token},
        headers={"X-Tenant-ID": str(tenant.id)},
    )
    assert denied.status_code == 401

    async with pg_session_maker() as db:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        row = (
            await db.execute(
                select(UserSession).where(UserSession.token_hash == token_hash)
            )
        ).scalar_one()
        assert row.user_id == user.id
        assert row.auth_level == "mfa_setup"


@pytest.mark.asyncio
async def test_privileged_mfa_enrollment_promotes_restricted_session(
    api_client, pg_session_maker
):
    email = f"mfa-promote-{uuid4().hex[:8]}@example.com"
    password = "MfaPassword1!"
    async with pg_session_maker() as db:
        _user, tenant = await _seed_user(
            db,
            email=email,
            password=password,
            role_name="GYM_OWNER",
        )

    csrf = await api_client.get("/api/v1/auth/csrf")
    csrf_token = csrf.json()["csrf_token"]
    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.json()["mfa_enrollment_required"] is True

    setup = await api_client.post(
        "/api/v1/auth/mfa/setup",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert setup.status_code == 200, setup.text
    code = pyotp.TOTP(setup.json()["secret"]).now()

    verify = await api_client.post(
        "/api/v1/auth/mfa/verify",
        json={"code": code},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert verify.status_code == 200, verify.text

    me = await api_client.get(
        "/api/v1/me/session",
        headers={"X-Tenant-ID": str(tenant.id)},
    )
    assert me.status_code == 200, me.text


@pytest.mark.asyncio
async def test_front_desk_login_without_enrollment_gets_restricted_session(
    api_client, pg_session_maker
):
    email = f"fd-enroll-{uuid4().hex[:8]}@example.com"
    password = "MfaPassword1!"
    async with pg_session_maker() as db:
        await _seed_user(db, email=email, password=password, role_name="FRONT_DESK")

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    assert login.json()["mfa_enrollment_required"] is True


@pytest.mark.asyncio
async def test_member_login_does_not_require_mfa_enrollment(
    api_client, pg_session_maker
):
    email = f"member-plain-{uuid4().hex[:8]}@example.com"
    password = "MfaPassword1!"
    async with pg_session_maker() as db:
        await _seed_user(db, email=email, password=password, role_name="MEMBER")

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    assert login.json()["mfa_enrollment_required"] is False
