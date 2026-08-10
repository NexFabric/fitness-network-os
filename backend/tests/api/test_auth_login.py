"""Public auth API — POST /auth/login, POST /auth/logout, GET /auth/me (real PG)."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.db.session import get_db
from app.main import app
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


async def _create_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    is_active: bool = True,
) -> User:
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash(password),
        is_active=is_active,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_login_success_returns_token_and_sets_cookie(
    api_client: AsyncClient, pg_session_maker
):
    email = f"login-{uuid4().hex[:8]}@example.com"
    password = "correct-horse-battery"
    async with pg_session_maker() as db:
        user = await _create_user(db, email=email, password=password)

    resp = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token"]
    assert body["user"]["id"] == str(user.id)
    assert body["user"]["email"] == email.lower()
    assert body["user"]["is_active"] is True
    assert "expires_at" in body

    # Cookie path preserved for browser clients
    assert "session_token" in resp.cookies
    assert resp.cookies["session_token"] == body["token"]

    # Session row stored as hash only
    token_hash = hashlib.sha256(body["token"].encode()).hexdigest()
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
async def test_login_email_normalized_case(api_client: AsyncClient, pg_session_maker):
    email = f"CaseMix-{uuid4().hex[:8]}@Example.COM"
    password = "pw-secret-1"
    async with pg_session_maker() as db:
        await _create_user(db, email=email.lower(), password=password)

    resp = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email.upper(), "password": password},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["email"] == email.lower()


@pytest.mark.asyncio
async def test_login_bad_password(api_client: AsyncClient, pg_session_maker):
    email = f"badpw-{uuid4().hex[:8]}@example.com"
    async with pg_session_maker() as db:
        await _create_user(db, email=email, password="right-password")

    resp = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrong-password"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_unknown_email(api_client: AsyncClient):
    resp = await api_client.post(
        "/api/v1/auth/login",
        json={"email": f"nobody-{uuid4().hex}@example.com", "password": "x"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_inactive_user(api_client: AsyncClient, pg_session_maker):
    email = f"inactive-{uuid4().hex[:8]}@example.com"
    async with pg_session_maker() as db:
        await _create_user(db, email=email, password="pw", is_active=False)

    resp = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "pw"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_bearer_after_login(api_client: AsyncClient, pg_session_maker):
    email = f"me-{uuid4().hex[:8]}@example.com"
    password = "me-password"
    async with pg_session_maker() as db:
        user = await _create_user(db, email=email, password=password)

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    token = login.json()["token"]

    me = await api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200, me.text
    assert me.json()["id"] == str(user.id)
    assert me.json()["email"] == email.lower()


@pytest.mark.asyncio
async def test_me_with_cookie_after_login(api_client: AsyncClient, pg_session_maker):
    email = f"cookie-{uuid4().hex[:8]}@example.com"
    password = "cookie-password"
    async with pg_session_maker() as db:
        await _create_user(db, email=email, password=password)

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    # httpx stores Set-Cookie; subsequent requests should send session_token
    me = await api_client.get("/api/v1/auth/me")
    assert me.status_code == 200, me.text
    assert me.json()["email"] == email.lower()


@pytest.mark.asyncio
async def test_me_unauthenticated(api_client: AsyncClient):
    resp = await api_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_session_bearer(
    api_client: AsyncClient, pg_session_maker
):
    email = f"logout-{uuid4().hex[:8]}@example.com"
    password = "logout-password"
    async with pg_session_maker() as db:
        await _create_user(db, email=email, password=password)

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    out = await api_client.post("/api/v1/auth/logout", headers=headers)
    assert out.status_code == 200, out.text
    assert out.json()["ok"] is True

    me = await api_client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 401

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    async with pg_session_maker() as db:
        row = (
            await db.execute(
                select(UserSession).where(UserSession.token_hash == token_hash)
            )
        ).scalar_one()
        assert row.is_revoked is True


@pytest.mark.asyncio
async def test_logout_requires_auth(api_client: AsyncClient):
    resp = await api_client.post("/api/v1/auth/logout")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_existing_preseeded_session_still_works_bearer(
    api_client: AsyncClient, pg_session_maker
):
    """Bearer path used by existing tests must keep working without login API."""
    raw = f"tok_{uuid4().hex}"
    th = hashlib.sha256(raw.encode()).hexdigest()
    async with pg_session_maker() as db:
        user = User(
            email=f"preseed-{uuid4().hex[:8]}@example.com",
            hashed_password=get_password_hash("unused"),
            is_active=True,
        )
        db.add(user)
        await db.flush()
        db.add(
            UserSession(
                user_id=user.id,
                token_hash=th,
                expires_at=datetime.now(UTC) + timedelta(days=1),
                is_revoked=False,
            )
        )
        await db.commit()
        user_id = user.id

    me = await api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {raw}"},
    )
    assert me.status_code == 200
    assert me.json()["id"] == str(user_id)
