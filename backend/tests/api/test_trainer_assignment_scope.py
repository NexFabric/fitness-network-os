"""Scope.ASSIGNED enforcement — a TRAINER sees only its assigned members.

Before trainer_assignments existed, TRAINER held tenant-wide members:read and
could read every member in the tenant. The row scope now comes from data:
members:read grants the call, members:read:all grants the whole tenant, and a
reader without the latter is restricted to its assignments.
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
from app.models.member import Member
from app.models.organization import Organization
from app.models.rbac import Permission, Role, UserRole
from app.models.tenant import Tenant
from app.models.trainer_assignment import TrainerAssignment
from app.models.user import User, UserSession

TRAINER_PERMS = [
    "gym:read",
    "memberships:read",
    "checkins:read",
    "entitlements:read",
    "entitlements:check",
    "access:read",
    "members:read",
    "locations:read",
    "pt:read",
    "pt:write",
]

OWNER_PERMS = TRAINER_PERMS + ["members:read:all", "members:write", "staff:write"]


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
    db: AsyncSession, *, tenant_id, role_name: str, perm_names: list[str]
) -> tuple[User, str]:
    raw, th = _token_pair()
    user = User(
        email=f"{role_name.lower()}-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    role = Role(
        name=f"{role_name}-{uuid4().hex[:8]}",
        description=f"test clone of {role_name}",
        permissions=await _ensure_perms(db, perm_names),
    )
    db.add(role)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant_id))
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=th,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
    )
    await db.flush()
    return user, raw


async def _member(db: AsyncSession, tenant_id, suffix: str) -> Member:
    member = Member(
        tenant_id=tenant_id,
        member_number=f"M-{suffix}-{uuid4().hex[:6]}",
        first_name="Test",
        last_name=suffix,
        status="ACTIVE",
    )
    db.add(member)
    await db.flush()
    return member


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


async def _scenario(pg_engine):
    """One tenant, one trainer, two members, only the first assigned."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="TA Org", domain=f"ta-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="TA Tenant",
            organization_id=org.id,
            location_code=f"TA-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()

        assigned = await _member(db, tenant.id, "assigned")
        other = await _member(db, tenant.id, "other")

        trainer, trainer_token = await _user_with_role(
            db, tenant_id=tenant.id, role_name="TRAINER", perm_names=TRAINER_PERMS
        )
        _owner, owner_token = await _user_with_role(
            db, tenant_id=tenant.id, role_name="GYM_OWNER", perm_names=OWNER_PERMS
        )

        db.add(
            TrainerAssignment(
                tenant_id=tenant.id,
                trainer_user_id=trainer.id,
                member_id=assigned.id,
                is_active=True,
            )
        )
        await db.commit()

        return {
            "tenant_id": tenant.id,
            "trainer_id": trainer.id,
            "trainer_token": trainer_token,
            "owner_token": owner_token,
            "assigned_id": assigned.id,
            "other_id": other.id,
        }


@pytest.mark.asyncio
async def test_trainer_list_returns_only_assigned_members(api_client, pg_engine):
    s = await _scenario(pg_engine)
    headers = {
        "Authorization": f"Bearer {s['trainer_token']}",
        "X-Tenant-ID": str(s["tenant_id"]),
    }

    resp = await api_client.get("/api/v1/members", headers=headers)
    assert resp.status_code == 200
    ids = {row["id"] for row in resp.json()}
    assert str(s["assigned_id"]) in ids
    assert str(s["other_id"]) not in ids


@pytest.mark.asyncio
async def test_trainer_cannot_read_unassigned_member(api_client, pg_engine):
    s = await _scenario(pg_engine)
    headers = {
        "Authorization": f"Bearer {s['trainer_token']}",
        "X-Tenant-ID": str(s["tenant_id"]),
    }

    ok = await api_client.get(f"/api/v1/members/{s['assigned_id']}", headers=headers)
    assert ok.status_code == 200

    denied = await api_client.get(f"/api/v1/members/{s['other_id']}", headers=headers)
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_trainer_cannot_check_entitlements_of_unassigned_member(
    api_client, pg_engine
):
    s = await _scenario(pg_engine)
    headers = {
        "Authorization": f"Bearer {s['trainer_token']}",
        "X-Tenant-ID": str(s["tenant_id"]),
    }

    denied = await api_client.post(
        f"/api/v1/members/{s['other_id']}/entitlements/check",
        headers=headers,
        json={"action": "GYM_ENTRY", "quantity": 1},
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_staff_with_read_all_still_sees_every_member(api_client, pg_engine):
    """The scope must not regress tenant-wide staff."""
    s = await _scenario(pg_engine)
    headers = {
        "Authorization": f"Bearer {s['owner_token']}",
        "X-Tenant-ID": str(s["tenant_id"]),
    }

    resp = await api_client.get("/api/v1/members", headers=headers)
    assert resp.status_code == 200
    ids = {row["id"] for row in resp.json()}
    assert {str(s["assigned_id"]), str(s["other_id"])} <= ids


@pytest.mark.asyncio
async def test_trainer_cannot_assign_members_to_itself(api_client, pg_engine):
    """staff:write is the gate; TRAINER does not hold it."""
    s = await _scenario(pg_engine)
    headers = {
        "Authorization": f"Bearer {s['trainer_token']}",
        "X-Tenant-ID": str(s["tenant_id"]),
    }

    denied = await api_client.post(
        f"/api/v1/trainers/{s['trainer_id']}/members",
        headers=headers,
        json={"member_id": str(s["other_id"])},
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_unassign_revokes_access(api_client, pg_engine):
    s = await _scenario(pg_engine)
    trainer_headers = {
        "Authorization": f"Bearer {s['trainer_token']}",
        "X-Tenant-ID": str(s["tenant_id"]),
    }
    owner_headers = {
        "Authorization": f"Bearer {s['owner_token']}",
        "X-Tenant-ID": str(s["tenant_id"]),
    }

    before = await api_client.get(
        f"/api/v1/members/{s['assigned_id']}", headers=trainer_headers
    )
    assert before.status_code == 200

    removed = await api_client.delete(
        f"/api/v1/trainers/{s['trainer_id']}/members/{s['assigned_id']}",
        headers=owner_headers,
    )
    assert removed.status_code == 204

    after = await api_client.get(
        f"/api/v1/members/{s['assigned_id']}", headers=trainer_headers
    )
    assert after.status_code == 403


@pytest.mark.asyncio
async def test_trainer_cannot_search_reception(api_client, pg_engine):
    s = await _scenario(pg_engine)
    headers = {
        "Authorization": f"Bearer {s['trainer_token']}",
        "X-Tenant-ID": str(s["tenant_id"]),
    }

    denied = await api_client.get(
        "/api/v1/reception/search",
        headers=headers,
        params={"q": "Test"},
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_trainer_cannot_open_reception_member_card(api_client, pg_engine):
    s = await _scenario(pg_engine)
    headers = {
        "Authorization": f"Bearer {s['trainer_token']}",
        "X-Tenant-ID": str(s["tenant_id"]),
    }

    denied = await api_client.get(
        f"/api/v1/reception/member/{s['other_id']}",
        headers=headers,
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_trainer_cannot_list_import_batches(api_client, pg_engine):
    s = await _scenario(pg_engine)
    headers = {
        "Authorization": f"Bearer {s['trainer_token']}",
        "X-Tenant-ID": str(s["tenant_id"]),
    }

    denied = await api_client.get("/api/v1/import/batches", headers=headers)
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_trainer_cannot_book_pt_for_unassigned_member(api_client, pg_engine):
    from datetime import UTC, datetime, timedelta

    from app.models.location import Location

    s = await _scenario(pg_engine)
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        loc = Location(
            tenant_id=s["tenant_id"],
            name="PT Room",
            timezone="Europe/Istanbul",
        )
        db.add(loc)
        await db.commit()
        loc_id = loc.id

    start = datetime.now(UTC) + timedelta(days=2)
    denied = await api_client.post(
        "/api/v1/classes/pt/appointments",
        headers={
            "Authorization": f"Bearer {s['trainer_token']}",
            "X-Tenant-ID": str(s["tenant_id"]),
        },
        json={
            "trainer_user_id": str(s["trainer_id"]),
            "member_id": str(s["other_id"]),
            "location_id": str(loc_id),
            "start_time_utc": start.isoformat(),
            "end_time_utc": (start + timedelta(hours=1)).isoformat(),
        },
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_trainer_dashboard_hides_finance(api_client, pg_engine):
    s = await _scenario(pg_engine)
    resp = await api_client.get(
        "/api/v1/dashboard/kpis",
        headers={
            "Authorization": f"Bearer {s['trainer_token']}",
            "X-Tenant-ID": str(s["tenant_id"]),
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["finance_visible"] is False
    assert data["past_due_invoices_amount_minor"] == 0
    assert data["month_collected_amount_minor"] == 0
    assert data["total_outstanding_debt_minor"] == 0
