"""Bind a MEMBER login to an existing member profile."""

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
from app.models.member import Member
from app.models.organization import Organization
from app.models.rbac import Permission, Role, UserRole
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


async def _setup(pg_engine, *, email: str | None = "portal@example.com"):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    raw = f"tok_{uuid4().hex}"
    async with maker() as db:
        org = Organization(name="Portal Org", domain=f"po-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Portal T",
            organization_id=org.id,
            location_code=f"PO-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()
        actor = User(
            email=f"owner-{uuid4().hex[:8]}@example.com",
            hashed_password="x",
            is_active=True,
        )
        db.add(actor)
        await db.flush()
        role = Role(
            name=f"OWN-{uuid4().hex[:8]}",
            description="owner clone",
            permissions=await _ensure_perms(
                db, ["members:write", "members:read", "members:read:all"]
            ),
        )
        db.add(role)
        await db.flush()
        db.add(UserRole(user_id=actor.id, role_id=role.id, tenant_id=tenant.id))
        db.add(
            UserSession(
                user_id=actor.id,
                token_hash=hashlib.sha256(raw.encode()).hexdigest(),
                expires_at=datetime.now(UTC) + timedelta(days=1),
                auth_level="full",
            )
        )
        member = Member(
            tenant_id=tenant.id,
            member_number=f"M-{uuid4().hex[:6]}",
            first_name="Ada",
            last_name="Member",
            email=email,
            status="ACTIVE",
        )
        db.add(member)
        await db.commit()
        return tenant.id, member.id, raw


def _headers(token: str, tenant_id) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }


@pytest.mark.asyncio
async def test_portal_account_binds_member_and_returns_otp(api_client, pg_engine):
    tenant_id, member_id, token = await _setup(pg_engine)
    res = await api_client.post(
        f"/api/v1/members/{member_id}/portal-account",
        headers=_headers(token, tenant_id),
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["member_id"] == str(member_id)
    assert body["email"] == "portal@example.com"
    assert "one_time_password" not in body
    assert body["invite_token"]
    assert res.headers["cache-control"] == "no-store"

    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        member = await db.get(Member, member_id)
        assert member is not None
        assert str(member.user_id) == body["user_id"]
        role = (
            await db.execute(select(Role).where(Role.name == "MEMBER"))
        ).scalar_one()
        link = (
            await db.execute(
                select(UserRole).where(
                    UserRole.user_id == member.user_id,
                    UserRole.role_id == role.id,
                    UserRole.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert link is not None


@pytest.mark.asyncio
async def test_portal_account_requires_email(api_client, pg_engine):
    tenant_id, member_id, token = await _setup(pg_engine, email=None)
    res = await api_client.post(
        f"/api/v1/members/{member_id}/portal-account",
        headers=_headers(token, tenant_id),
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "member_email_required"


@pytest.mark.asyncio
async def test_portal_account_conflict_when_already_bound(api_client, pg_engine):
    tenant_id, member_id, token = await _setup(pg_engine)
    first = await api_client.post(
        f"/api/v1/members/{member_id}/portal-account",
        headers=_headers(token, tenant_id),
    )
    assert first.status_code == 201, first.text
    again = await api_client.post(
        f"/api/v1/members/{member_id}/portal-account",
        headers=_headers(token, tenant_id),
    )
    assert again.status_code == 409
    assert again.json()["detail"] == "portal_already_bound"
