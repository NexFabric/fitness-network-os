"""DSAR v1: bound member can package their data; staff can list the tenant."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import get_db
from app.main import app
from app.models.finance import BillingAccount, Invoice
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


async def _actor(db, *, tenant_id, perms: list[str], email: str | None = None):
    raw = f"tok_{uuid4().hex}"
    user = User(
        email=email or f"dsar-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    role = Role(
        name=f"DSAR-{uuid4().hex[:8]}",
        description="dsar",
        permissions=await _ensure_perms(db, perms),
    )
    db.add(role)
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


async def _setup(pg_engine):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="DSAR Org", domain=f"dsar-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="DSAR T",
            organization_id=org.id,
            location_code=f"DS-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()
        member_user, member_token = await _actor(
            db,
            tenant_id=tenant.id,
            perms=["profile:read", "finance:read:self"],
        )
        member = Member(
            tenant_id=tenant.id,
            member_number=f"D-{uuid4().hex[:6]}",
            first_name="Data",
            last_name="Subject",
            email="subject@example.com",
            status="ACTIVE",
            user_id=member_user.id,
        )
        db.add(member)
        await db.flush()
        account = BillingAccount(tenant_id=tenant.id, member_id=member.id)
        db.add(account)
        await db.flush()
        db.add(
            Invoice(
                tenant_id=tenant.id,
                billing_account_id=account.id,
                status="OPEN",
                total_amount_minor=19900,
                paid_amount_minor=0,
                discount_amount_minor=0,
                currency="TRY",
            )
        )
        _staff, staff_token = await _actor(
            db, tenant_id=tenant.id, perms=["members:read:all"]
        )
        other_tenant = Tenant(
            id=uuid4(),
            name="Other",
            organization_id=org.id,
            location_code=f"OT-{uuid4().hex[:6]}",
        )
        db.add(other_tenant)
        await db.flush()
        _other_staff, other_token = await _actor(
            db, tenant_id=other_tenant.id, perms=["members:read:all"]
        )
        await db.commit()
        return {
            "tenant_id": tenant.id,
            "member_id": member.id,
            "member_token": member_token,
            "staff_token": staff_token,
            "other_token": other_token,
        }


def _headers(token: str, tenant_id) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


@pytest.mark.asyncio
async def test_bound_member_export_contains_email_and_integer_money(
    api_client, pg_engine
):
    ctx = await _setup(pg_engine)
    first = await api_client.post(
        "/api/v1/me/dsar/export",
        headers=_headers(ctx["member_token"], ctx["tenant_id"]),
    )
    assert first.status_code == 201, first.text
    body = first.json()
    assert body["kind"] == "EXPORT"
    assert body["status"] == "PACKAGED"
    assert body["created"] is True
    assert body["download_url"]

    again = await api_client.post(
        "/api/v1/me/dsar/export",
        headers=_headers(ctx["member_token"], ctx["tenant_id"]),
    )
    assert again.status_code == 201
    assert again.json()["created"] is False
    assert again.json()["id"] == body["id"]

    listed = await api_client.get(
        "/api/v1/me/dsar",
        headers=_headers(ctx["member_token"], ctx["tenant_id"]),
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    from pathlib import Path
    from urllib.parse import unquote, urlparse

    from app.api.deps import current_tenant_id_var
    from app.services.dsar import DsarService

    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    token = current_tenant_id_var.set(ctx["tenant_id"])
    try:
        async with maker() as db:
            svc = DsarService(db)
            row = await svc.get(ctx["tenant_id"], body["id"])
            assert row is not None
            url = await svc.download_url(ctx["tenant_id"], row)
    finally:
        current_tenant_id_var.reset(token)

    assert url
    parsed = urlparse(url)
    assert parsed.scheme == "file"
    payload = json.loads(Path(unquote(parsed.path)).read_text())

    assert payload is not None
    assert payload["member"]["email"] == "subject@example.com"
    assert payload["invoices"][0]["total_amount_minor"] == 19900
    assert isinstance(payload["invoices"][0]["total_amount_minor"], int)
    blob = json.dumps(payload).lower()
    assert "one_time_password" not in blob
    assert "invite_token" not in blob


@pytest.mark.asyncio
async def test_staff_lists_tenant_dsar_other_tenant_empty(api_client, pg_engine):
    ctx = await _setup(pg_engine)
    await api_client.post(
        "/api/v1/me/dsar/export",
        headers=_headers(ctx["member_token"], ctx["tenant_id"]),
    )
    mine = await api_client.get(
        "/api/v1/admin/dsar",
        headers=_headers(ctx["staff_token"], ctx["tenant_id"]),
    )
    assert mine.status_code == 200, mine.text
    assert len(mine.json()) == 1

    other = await api_client.get(
        "/api/v1/admin/dsar",
        headers=_headers(ctx["other_token"], ctx["tenant_id"]),
    )
    # other staff is not a member of this tenant
    assert other.status_code == 403
