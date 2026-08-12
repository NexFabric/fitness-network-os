"""Federation read surface — scope, isolation and the ADR-031 aggregate loop."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import get_db
from app.main import app
from app.models.member import Member
from app.models.organization import Organization
from app.models.rbac import Permission, Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User, UserSession


def _token_pair() -> tuple[str, str]:
    raw = f"tok_{uuid4().hex}"
    return raw, hashlib.sha256(raw.encode()).hexdigest()


async def _ensure_perm(db: AsyncSession, name: str) -> Permission:
    row = (
        await db.execute(select(Permission).where(Permission.name == name))
    ).scalar_one_or_none()
    if row is None:
        row = Permission(name=name, description=name)
        db.add(row)
        await db.flush()
    return row


async def _principal(
    db: AsyncSession,
    *,
    role_name: str,
    tenant_id=None,
    organization_id=None,
    perms: list[str] | None = None,
) -> tuple[User, str]:
    raw, th = _token_pair()
    user = User(
        email=f"{role_name.lower()}-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    # get_federation_scope matches on the canonical role name, so reuse the
    # seeded role rather than cloning it under a unique name.
    role = (
        await db.execute(select(Role).where(Role.name == role_name))
    ).scalar_one_or_none()
    if role is None:
        role = Role(
            name=role_name,
            description=role_name,
            permissions=[await _ensure_perm(db, p) for p in (perms or [])],
        )
        db.add(role)
        await db.flush()
    db.add(
        UserRole(
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant_id,
            organization_id=organization_id,
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


async def _two_organizations(pg_engine):
    """Two orgs, one tenant each, with a different member count per tenant."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org_a = Organization(name="Fed A", domain=f"a-{uuid4().hex[:6]}.com")
        org_b = Organization(name="Fed B", domain=f"b-{uuid4().hex[:6]}.com")
        db.add_all([org_a, org_b])
        await db.flush()

        tenant_a = Tenant(
            id=uuid4(),
            name="A Club",
            organization_id=org_a.id,
            location_code=f"A-{uuid4().hex[:6]}",
        )
        tenant_b = Tenant(
            id=uuid4(),
            name="B Club",
            organization_id=org_b.id,
            location_code=f"B-{uuid4().hex[:6]}",
        )
        db.add_all([tenant_a, tenant_b])
        await db.flush()

        for i in range(3):
            db.add(
                Member(
                    tenant_id=tenant_a.id,
                    member_number=f"A{i}-{uuid4().hex[:6]}",
                    first_name="A",
                    last_name=str(i),
                    status="ACTIVE",
                )
            )
        db.add(
            Member(
                tenant_id=tenant_b.id,
                member_number=f"B0-{uuid4().hex[:6]}",
                first_name="B",
                last_name="0",
                status="ACTIVE",
            )
        )

        _fed_a, token_a = await _principal(
            db,
            role_name="FEDERATION_ANALYST",
            organization_id=org_a.id,
            perms=["federation:read", "gym:read"],
        )
        _staff, token_staff = await _principal(
            db,
            role_name="GYM_OWNER",
            tenant_id=tenant_a.id,
            perms=["members:read", "members:read:all"],
        )
        await db.commit()

        return {
            "org_a": org_a.id,
            "org_b": org_b.id,
            "tenant_a": tenant_a.id,
            "tenant_b": tenant_b.id,
            "fed_a_token": token_a,
            "staff_token": token_staff,
        }


@pytest.mark.asyncio
async def test_federation_analyst_sees_only_its_own_organization(
    api_client, pg_engine
):
    s = await _two_organizations(pg_engine)
    headers = {"Authorization": f"Bearer {s['fed_a_token']}"}

    resp = await api_client.get("/api/v1/admin/tenants", headers=headers)
    assert resp.status_code == 200
    ids = {row["id"] for row in resp.json()}
    assert str(s["tenant_a"]) in ids
    assert str(s["tenant_b"]) not in ids


@pytest.mark.asyncio
async def test_out_of_scope_tenant_is_404_not_403(api_client, pg_engine):
    """A 403 would confirm the tenant exists; scope leaks must not be probeable."""
    s = await _two_organizations(pg_engine)
    headers = {"Authorization": f"Bearer {s['fed_a_token']}"}

    resp = await api_client.get(
        f"/api/v1/admin/tenants/{s['tenant_b']}", headers=headers
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_tenant_staff_cannot_reach_federation_surface(api_client, pg_engine):
    s = await _two_organizations(pg_engine)
    headers = {"Authorization": f"Bearer {s['staff_token']}"}

    resp = await api_client.get("/api/v1/admin/tenants", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_federation_surface_is_401(api_client):
    resp = await api_client.get("/api/v1/admin/tenants")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_aggregate_counts_are_per_tenant_correct(api_client, pg_engine):
    """Proves the per-tenant loop isolates: A's 3 members never bleed into B."""
    s = await _two_organizations(pg_engine)
    headers = {"Authorization": f"Bearer {s['fed_a_token']}"}

    resp = await api_client.get(
        f"/api/v1/admin/tenants/{s['tenant_a']}", headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["member_count"] == 3
    assert body["revenue_minor"] == 0


@pytest.mark.asyncio
async def test_aggregate_loop_clears_tenant_context(api_client, pg_engine):
    """ADR-031: the GUC must not outlive the loop."""
    from app.services.federation import FederationService

    s = await _two_organizations(pg_engine)
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        await FederationService(db).metrics_for_tenants(
            [s["tenant_a"], s["tenant_b"]]
        )
        leftover = (
            await db.execute(
                text("SELECT current_setting('app.current_tenant_id', true)")
            )
        ).scalar_one()
        assert leftover in ("", None)


@pytest.mark.asyncio
async def test_aggregate_loop_refuses_oversized_page(pg_engine):
    from app.services.federation import MAX_TENANT_PAGE, FederationService

    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        with pytest.raises(ValueError):
            await FederationService(db).metrics_for_tenants(
                [uuid4() for _ in range(MAX_TENANT_PAGE + 1)]
            )
