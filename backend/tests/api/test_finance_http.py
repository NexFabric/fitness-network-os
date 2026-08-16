"""HTTP coverage for finance endpoints (billing, invoice, payment, list)."""

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
    db: AsyncSession, *, tenant_id, perm_names: list[str]
) -> tuple[User, str]:
    raw, th = _token_pair()
    user = User(
        email=f"fin-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    perms = await _ensure_perms(db, perm_names)
    role = Role(
        name=f"FIN-{uuid4().hex[:8]}",
        description="finance http",
        permissions=perms,
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
async def test_finance_http_invoice_payment_and_lists(api_client, pg_engine):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Fin HTTP Org", domain=f"finh-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Fin HTTP T",
            organization_id=org.id,
            location_code=f"FH-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()
        member = Member(
            id=uuid4(),
            tenant_id=tenant.id,
            member_number=f"M-{uuid4().hex[:6]}",
            first_name="Pay",
            last_name="Http",
            email=f"pay-{uuid4().hex[:6]}@example.com",
        )
        db.add(member)
        _user, token = await _user_with_role(
            db,
            tenant_id=tenant.id,
            perm_names=[
                "finance:read",
                "finance:write",
                "finance:refund",
                "finance:credit",
                "finance:manage",
                "finance:reconcile",
            ],
        )
        await db.commit()
        tenant_id = tenant.id
        member_id = member.id

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }

    denied = await api_client.post(
        "/api/v1/finance/billing-accounts",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(uuid4())},
        json={"member_id": str(member_id), "currency": "TRY"},
    )
    assert denied.status_code in {403, 404}

    account_res = await api_client.post(
        "/api/v1/finance/billing-accounts",
        headers=headers,
        json={"member_id": str(member_id), "currency": "TRY"},
    )
    assert account_res.status_code == 200, account_res.text
    account_id = account_res.json()["id"]

    inv_res = await api_client.post(
        "/api/v1/finance/invoices",
        headers=headers,
        json={
            "billing_account_id": account_id,
            "items": [
                {
                    "description": "Monthly",
                    "unit_amount_minor": 10000,
                    "quantity": 1,
                }
            ],
            "issue": True,
        },
    )
    assert inv_res.status_code == 200, inv_res.text
    invoice_id = inv_res.json()["id"]
    assert inv_res.json()["total_amount_minor"] == 10000

    listed = await api_client.get("/api/v1/finance/invoices", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    missing_key = await api_client.post(
        "/api/v1/finance/payments",
        headers=headers,
        json={
            "billing_account_id": account_id,
            "amount_minor": 10000,
            "method": "CASH",
            "allocations": [{"invoice_id": invoice_id, "amount_minor": 10000}],
        },
    )
    assert missing_key.status_code == 400

    pay_headers = {**headers, "Idempotency-Key": f"pay-{uuid4().hex}"}
    pay_res = await api_client.post(
        "/api/v1/finance/payments",
        headers=pay_headers,
        json={
            "billing_account_id": account_id,
            "amount_minor": 10000,
            "method": "CASH",
            "allocations": [{"invoice_id": invoice_id, "amount_minor": 10000}],
        },
    )
    assert pay_res.status_code == 200, pay_res.text
    replay = await api_client.post(
        "/api/v1/finance/payments",
        headers=pay_headers,
        json={
            "billing_account_id": account_id,
            "amount_minor": 10000,
            "method": "CASH",
            "allocations": [{"invoice_id": invoice_id, "amount_minor": 10000}],
        },
    )
    assert replay.status_code == 200
    assert replay.json()["id"] == pay_res.json()["id"]

    pays = await api_client.get("/api/v1/finance/payments", headers=headers)
    assert pays.status_code == 200
    assert pays.json()["total"] >= 1

    disc = await api_client.post(
        "/api/v1/finance/discounts",
        headers=headers,
        json={"code": "HTTP10", "name": "Http ten", "percent_bps": 1000},
    )
    assert disc.status_code == 200, disc.text
