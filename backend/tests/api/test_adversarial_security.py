"""Adversarial penetration and security boundary verification suite.

Tests real attack vectors:
1. Cross-tenant IDOR/BOLA attempts on members
2. Forged and tampered bearer tokens
3. Revoked and expired session enforcement
4. Superuser mutation without break-glass
"""

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
from app.models.location import Location
from app.models.member import Member
from app.models.organization import Organization
from app.models.rbac import Permission, Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User, UserSession


def _token_pair() -> tuple[str, str]:
    raw = f"tok_adv_{uuid4().hex}"
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


async def _create_test_tenant(
    db: AsyncSession,
    *,
    prefix: str,
    perm_names: list[str],
    is_revoked: bool = False,
    expires_at: datetime | None = None,
) -> tuple[Tenant, User, str, Member]:
    org = Organization(name=f"Org {prefix}", domain=f"{prefix}-{uuid4().hex[:6]}.org")
    db.add(org)
    await db.flush()

    tenant = Tenant(
        id=uuid4(),
        name=f"Tenant {prefix}",
        organization_id=org.id,
        location_code=f"ADV-{uuid4().hex[:6]}",
    )
    db.add(tenant)
    await db.flush()

    user = User(
        email=f"{prefix}-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    perms = await _ensure_perms(db, perm_names)
    role = Role(
        name=f"Role-{prefix}-{uuid4().hex[:8]}",
        description=f"Adversarial role for {prefix}",
        permissions=perms,
    )
    db.add(role)
    await db.flush()

    db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant.id))

    raw_tok, th = _token_pair()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=th,
            auth_level="full",
            expires_at=expires_at or (datetime.now(UTC) + timedelta(hours=2)),
            is_revoked=is_revoked,
            last_seen_at=datetime.now(UTC),
        )
    )

    location = Location(
        tenant_id=tenant.id,
        name="Main Branch",
        timezone="UTC",
    )
    db.add(location)
    await db.flush()

    member = Member(
        tenant_id=tenant.id,
        first_name="Athlete",
        last_name=prefix,
        member_number=f"M-{uuid4().hex[:6]}",
        email=f"ath-{prefix}-{uuid4().hex[:6]}@example.com",
    )
    db.add(member)
    await db.flush()

    return tenant, user, raw_tok, member


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
async def test_adversarial_penetration_suite(api_client, pg_engine):
    """Unified adversarial security suite covering BOLA, token forgery, revoked/expired sessions, and superuser break-glass."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        # Tenant A (Desk staff)
        t_a, _, tok_a, _ = await _create_test_tenant(
            db,
            prefix="adv-a",
            perm_names=[
                "members:read",
                "members:write",
                "reception:read",
                "members:read:all",
            ],
        )
        # Tenant B (Target member)
        t_b, _, _, m_b = await _create_test_tenant(
            db,
            prefix="adv-b",
            perm_names=["members:read", "members:read:all"],
        )
        # Revoked session user
        _, _, tok_revoked, _ = await _create_test_tenant(
            db,
            prefix="adv-revoked",
            perm_names=["members:read"],
            is_revoked=True,
        )
        # Expired session user
        _, _, tok_expired, _ = await _create_test_tenant(
            db,
            prefix="adv-expired",
            perm_names=["members:read"],
            expires_at=datetime.now(UTC) - timedelta(minutes=15),
        )
        # Superuser (without break-glass)
        su = User(
            email=f"su-adv-{uuid4().hex[:8]}@example.com",
            hashed_password="x",
            is_superuser=True,
            is_active=True,
        )
        db.add(su)
        await db.flush()
        raw_tok_su, th_su = _token_pair()
        db.add(
            UserSession(
                user_id=su.id,
                token_hash=th_su,
                auth_level="full",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                is_revoked=False,
                last_seen_at=datetime.now(UTC),
            )
        )
        await db.commit()

    # Vector 1: Cross-tenant IDOR — Tenant A tries to read Tenant B's member under Tenant A header -> 404
    r1 = await api_client.get(
        f"/api/v1/members/{m_b.id}",
        headers={"Authorization": f"Bearer {tok_a}", "X-Tenant-ID": str(t_a.id)},
    )
    assert r1.status_code in (403, 404), f"Cross-tenant IDOR leak: {r1.status_code}"

    # Vector 2: Tenant Forgery — Tenant A tries to forge X-Tenant-ID to Tenant B -> 401/403
    r2 = await api_client.get(
        f"/api/v1/members/{m_b.id}",
        headers={"Authorization": f"Bearer {tok_a}", "X-Tenant-ID": str(t_b.id)},
    )
    assert r2.status_code in (401, 403), (
        f"Tenant forgery must be rejected: {r2.status_code}"
    )

    # Vector 3: Forged / Arbitrary token attack -> 401
    r3 = await api_client.get(
        "/api/v1/me/session",
        headers={"Authorization": "Bearer forged_random_token_12345"},
    )
    assert r3.status_code == 401

    # Vector 4: Revoked session attack -> 401
    r4 = await api_client.get(
        "/api/v1/me/session",
        headers={"Authorization": f"Bearer {tok_revoked}"},
    )
    assert r4.status_code == 401

    # Vector 5: Expired session attack -> 401
    r5 = await api_client.get(
        "/api/v1/me/session",
        headers={"Authorization": f"Bearer {tok_expired}"},
    )
    assert r5.status_code == 401

    # Vector 6: Superuser mutating tenant resource without break-glass -> 403
    r6 = await api_client.post(
        "/api/v1/members",
        headers={"Authorization": f"Bearer {raw_tok_su}", "X-Tenant-ID": str(t_a.id)},
        json={
            "first_name": "Injected",
            "last_name": "Member",
            "member_number": f"INJ-{uuid4().hex[:4]}",
        },
    )
    assert r6.status_code in (403, 401), (
        f"Superuser write without BG must fail: {r6.status_code}"
    )
