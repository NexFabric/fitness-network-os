"""Trainer directory — RBAC mapping + tenant isolation.

``GET /classes/trainers`` is the class/PT picker source. It must list users
holding the canonical TRAINER role in the caller's tenant and must not leak
another tenant's trainers. Members use ``pt:book:self`` (with owner proof),
not ``staff:read``.
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
from app.models.organization import Organization
from app.models.rbac import Permission, Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User, UserSession

MEMBER_PERMS = ["pt:book:self", "pt:read:self", "classes:read:self"]
OWNER_PERMS = ["staff:read", "classes:read", "classes:write", "pt:read"]


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


def _headers(token: str, tenant_id) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }


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


async def _canonical_role(db: AsyncSession, name: str, perm_names: list[str]) -> Role:
    role = (
        await db.execute(select(Role).where(Role.name == name))
    ).scalar_one_or_none()
    if role is not None:
        return role
    role = Role(
        name=name,
        description=name,
        is_system=True,
        permissions=await _ensure_perms(db, perm_names),
    )
    db.add(role)
    await db.flush()
    return role


async def _login(db: AsyncSession, *, tenant_id, email: str, role: Role) -> tuple[User, str]:
    raw = f"tok_{uuid4().hex}"
    user = User(email=email, hashed_password="x", is_active=True)
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant_id))
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            auth_level="full",
        )
    )
    await db.flush()
    return user, raw


async def _tenant(db: AsyncSession, label: str) -> Tenant:
    org = Organization(name=f"{label} Org", domain=f"{label}-{uuid4().hex[:6]}.com")
    db.add(org)
    await db.flush()
    tenant = Tenant(
        id=uuid4(),
        name=f"{label} Tenant",
        organization_id=org.id,
        location_code=f"{label[:2].upper()}-{uuid4().hex[:6]}",
    )
    db.add(tenant)
    await db.flush()
    return tenant


@pytest.mark.asyncio
async def test_member_sees_same_tenant_trainers_by_email(api_client, pg_engine):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        tenant_a = await _tenant(db, "DirA")
        tenant_b = await _tenant(db, "DirB")
        trainer_role = await _canonical_role(db, "TRAINER", ["pt:read", "pt:write"])
        member_role = await _canonical_role(db, "MEMBER", MEMBER_PERMS)
        owner_role = await _canonical_role(db, "GYM_OWNER", OWNER_PERMS)

        trainer_a, _ = await _login(
            db,
            tenant_id=tenant_a.id,
            email=f"trainer-a-{uuid4().hex[:6]}@e2e.local",
            role=trainer_role,
        )
        trainer_b, _ = await _login(
            db,
            tenant_id=tenant_b.id,
            email=f"trainer-b-{uuid4().hex[:6]}@e2e.local",
            role=trainer_role,
        )
        _member, member_token = await _login(
            db,
            tenant_id=tenant_a.id,
            email=f"member-a-{uuid4().hex[:6]}@e2e.local",
            role=member_role,
        )
        _owner, owner_token = await _login(
            db,
            tenant_id=tenant_a.id,
            email=f"owner-a-{uuid4().hex[:6]}@e2e.local",
            role=owner_role,
        )
        await db.commit()

    member_list = await api_client.get(
        "/api/v1/classes/trainers", headers=_headers(member_token, tenant_a.id)
    )
    assert member_list.status_code == 200, member_list.text
    emails = {row["email"] for row in member_list.json()}
    assert trainer_a.email in emails
    assert trainer_b.email not in emails
    assert all(row["role"] == "TRAINER" for row in member_list.json())

    owner_list = await api_client.get(
        "/api/v1/classes/trainers", headers=_headers(owner_token, tenant_a.id)
    )
    assert owner_list.status_code == 200, owner_list.text
    owner_emails = {row["email"] for row in owner_list.json()}
    assert trainer_a.email in owner_emails
    assert trainer_b.email not in owner_emails

    # Tenant header for B with tenant-A credentials must not reveal B's trainer.
    crossed = await api_client.get(
        "/api/v1/classes/trainers", headers=_headers(member_token, tenant_b.id)
    )
    assert crossed.status_code in {200, 403}
    if crossed.status_code == 200:
        assert trainer_b.email not in {row["email"] for row in crossed.json()}


@pytest.mark.asyncio
async def test_session_rejects_trainer_from_another_tenant(api_client, pg_engine):
    from app.models.booking import ClassType
    from app.models.location import Location

    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        tenant_a = await _tenant(db, "SessA")
        tenant_b = await _tenant(db, "SessB")
        trainer_role = await _canonical_role(db, "TRAINER", ["pt:read", "pt:write"])
        owner_role = await _canonical_role(db, "GYM_OWNER", OWNER_PERMS)
        foreign, _ = await _login(
            db,
            tenant_id=tenant_b.id,
            email=f"foreign-{uuid4().hex[:6]}@e2e.local",
            role=trainer_role,
        )
        _owner, owner_token = await _login(
            db,
            tenant_id=tenant_a.id,
            email=f"owner-s-{uuid4().hex[:6]}@e2e.local",
            role=owner_role,
        )
        loc = Location(
            id=uuid4(),
            tenant_id=tenant_a.id,
            name="Studio",
            timezone="Europe/Istanbul",
        )
        db.add(loc)
        ctype = ClassType(
            tenant_id=tenant_a.id,
            name="HIIT",
            category="CARDIO",
            duration_minutes=45,
            default_capacity=8,
        )
        db.add(ctype)
        await db.commit()
        loc_id, type_id = loc.id, ctype.id

    start = datetime.now(UTC) + timedelta(days=1)
    res = await api_client.post(
        "/api/v1/classes/sessions",
        headers=_headers(owner_token, tenant_a.id),
        json={
            "location_id": str(loc_id),
            "class_type_id": str(type_id),
            "trainer_user_id": str(foreign.id),
            "start_time_utc": start.isoformat(),
            "end_time_utc": (start + timedelta(minutes=45)).isoformat(),
            "capacity": 8,
        },
    )
    assert res.status_code == 400, res.text
    assert "Eğitmen" in res.json()["detail"]
