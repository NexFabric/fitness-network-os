"""Phase 15.5C — public outbox removed + MEMBER horizontal auth (BOLA) closed."""

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
    # Role.name is globally unique — use unique names; authz matches permissions, not role id.
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


@pytest.mark.asyncio
async def test_public_outbox_routes_absent(api_client):
    """Generic event inject surface must not exist on /api/v1."""
    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/api/v1/outbox/events" not in paths
    assert "/api/v1/outbox/inbox" not in paths
    # Unauthenticated still must not hit a live route (404 not 401/403 with body inject)
    r1 = await api_client.post(
        "/api/v1/outbox/events", json={"event_type": "x", "payload": {}}
    )
    r2 = await api_client.post(
        "/api/v1/outbox/inbox",
        json={"event_id": "1", "event_type": "x", "payload": {}},
    )
    assert r1.status_code == 404
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_member_cannot_check_other_member_entitlement(api_client, pg_engine):
    """BOLA: MEMBER A must not check Member B via staff path; /me only for self."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="BOLA Org", domain=f"bola-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="BOLA T",
            organization_id=org.id,
            location_code=f"B-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()

        member_self_perms = [
            "profile:read",
            "profile:write",
            "memberships:read:self",
            "checkins:read:self",
            "checkins:write:self",
            "entitlements:read:self",
            "entitlements:check:self",
            "access:issue:self",
        ]
        staff_perms = [
            "entitlements:check",
            "entitlements:read",
            "members:read",
        ]

        user_a, token_a = await _user_with_role(
            db,
            tenant_id=tenant.id,
            role_name="MEMBER",
            perm_names=member_self_perms,
            email_prefix="mem-a",
        )
        user_b, _token_b = await _user_with_role(
            db,
            tenant_id=tenant.id,
            role_name="MEMBER",
            perm_names=member_self_perms,
            email_prefix="mem-b",
        )
        _staff, token_staff = await _user_with_role(
            db,
            tenant_id=tenant.id,
            role_name="GYM_ADMIN",
            perm_names=staff_perms,
            email_prefix="staff",
        )

        member_a = Member(
            id=uuid4(),
            tenant_id=tenant.id,
            member_number=f"A-{uuid4().hex[:6]}",
            first_name="A",
            last_name="Mem",
            status="ACTIVE",
            user_id=user_a.id,
        )
        member_b = Member(
            id=uuid4(),
            tenant_id=tenant.id,
            member_number=f"B-{uuid4().hex[:6]}",
            first_name="B",
            last_name="Mem",
            status="ACTIVE",
            user_id=user_b.id,
        )
        db.add_all([member_a, member_b])
        await db.commit()
        tenant_id = tenant.id
        member_a_id = member_a.id
        member_b_id = member_b.id

    headers_a = {
        "Authorization": f"Bearer {token_a}",
        "X-Tenant-ID": str(tenant_id),
    }
    headers_staff = {
        "Authorization": f"Bearer {token_staff}",
        "X-Tenant-ID": str(tenant_id),
    }
    body = {"action": "GYM_ENTRY", "quantity": 1}

    # A → B staff path DENY
    deny_b = await api_client.post(
        f"/api/v1/members/{member_b_id}/entitlements/check",
        headers=headers_a,
        json=body,
    )
    assert deny_b.status_code == 403

    # A → A staff path also DENY (MEMBER has no entitlements:check)
    deny_a_staff = await api_client.post(
        f"/api/v1/members/{member_a_id}/entitlements/check",
        headers=headers_a,
        json=body,
    )
    assert deny_a_staff.status_code == 403

    # A → /me ALLOW (authz passes; entitlement business may be not entitled)
    me_ok = await api_client.post(
        "/api/v1/me/entitlements/check",
        headers=headers_a,
        json=body,
    )
    assert me_ok.status_code == 200
    me_json = me_ok.json()
    assert me_json["member_id"] == str(member_a_id)
    assert "granted" in me_json

    # Staff → B ALLOW (authz)
    staff_ok = await api_client.post(
        f"/api/v1/members/{member_b_id}/entitlements/check",
        headers=headers_staff,
        json=body,
    )
    assert staff_ok.status_code == 200


@pytest.mark.asyncio
async def test_me_entitlements_unbound_member_404(api_client, pg_engine):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Unbound Org", domain=f"ub-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Unbound T",
            organization_id=org.id,
            location_code=f"U-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()
        _user, token = await _user_with_role(
            db,
            tenant_id=tenant.id,
            role_name="MEMBER",
            perm_names=["entitlements:check:self"],
            email_prefix="unbound",
        )
        await db.commit()
        tenant_id = tenant.id

    r = await api_client.post(
        "/api/v1/me/entitlements/check",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant_id),
        },
        json={"action": "GYM_ENTRY", "quantity": 1},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "member_not_bound"


@pytest.mark.asyncio
async def test_gym_owner_yaml_lacks_outbox_write():
    """Static matrix: tenant gym roles cannot inject events."""
    from pathlib import Path

    import yaml

    data = yaml.safe_load(
        (Path(__file__).resolve().parents[2] / "permissions.yml").read_text()
    )
    for role in ("GYM_OWNER", "GYM_ADMIN", "GYM_MANAGER"):
        perms = set(data["roles"][role]["permissions"])
        assert "outbox:write" not in perms, role
        assert "inbox:write" not in perms, role
        assert "outbox:read" not in perms, role
        assert "inbox:read" not in perms, role
