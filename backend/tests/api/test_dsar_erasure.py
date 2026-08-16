"""DSAR erasure: open invoices hold; paid invoices stay after anonymize."""

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
        email=email or f"erase-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    role = Role(
        name=f"ERASE-{uuid4().hex[:8]}",
        description="dsar-erasure",
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


async def _setup(pg_engine, *, invoice_status: str):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Erase Org", domain=f"er-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Erase T",
            organization_id=org.id,
            location_code=f"ER-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()
        member_user, member_token = await _actor(
            db,
            tenant_id=tenant.id,
            perms=["profile:read", "profile:write", "finance:read:self"],
        )
        member = Member(
            tenant_id=tenant.id,
            member_number=f"E-{uuid4().hex[:6]}",
            first_name="Silinecek",
            last_name="Kisi",
            email="erase-me@example.com",
            phone="+905551112233",
            status="ACTIVE",
            user_id=member_user.id,
        )
        db.add(member)
        await db.flush()
        account = BillingAccount(tenant_id=tenant.id, member_id=member.id)
        db.add(account)
        await db.flush()
        invoice = Invoice(
            tenant_id=tenant.id,
            billing_account_id=account.id,
            status=invoice_status,
            total_amount_minor=19900,
            paid_amount_minor=19900 if invoice_status == "PAID" else 0,
            discount_amount_minor=0,
            currency="TRY",
        )
        db.add(invoice)
        await db.flush()
        await db.commit()
        return {
            "tenant_id": tenant.id,
            "member_id": member.id,
            "member_token": member_token,
            "invoice_id": invoice.id,
            "user_id": member_user.id,
        }


def _headers(token: str, tenant_id) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


@pytest.mark.asyncio
async def test_open_invoice_holds_erasure(api_client, pg_engine):
    ctx = await _setup(pg_engine, invoice_status="OPEN")
    res = await api_client.post(
        "/api/v1/me/dsar/erasure",
        headers=_headers(ctx["member_token"], ctx["tenant_id"]),
    )
    assert res.status_code == 409, res.text
    assert res.json()["detail"] == "legal_hold_open_invoices"

    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        member = await db.get(Member, ctx["member_id"])
        assert member is not None
        assert member.email == "erase-me@example.com"
        assert member.first_name == "Silinecek"
        invoice = await db.get(Invoice, ctx["invoice_id"])
        assert invoice is not None
        assert invoice.status == "OPEN"
        assert invoice.total_amount_minor == 19900


@pytest.mark.asyncio
async def test_paid_invoice_stays_after_anonymize(api_client, pg_engine):
    ctx = await _setup(pg_engine, invoice_status="PAID")
    first = await api_client.post(
        "/api/v1/me/dsar/erasure",
        headers=_headers(ctx["member_token"], ctx["tenant_id"]),
    )
    assert first.status_code == 201, first.text
    body = first.json()
    assert body["kind"] == "ERASURE"
    assert body["status"] == "COMPLETED"
    assert body["created"] is True

    again = await api_client.post(
        "/api/v1/me/dsar/erasure",
        headers=_headers(ctx["member_token"], ctx["tenant_id"]),
    )
    # user is unbound + deactivated; session still valid until revoked check
    # after first call the session is revoked so a second call is 401
    assert again.status_code in (201, 401)
    if again.status_code == 201:
        assert again.json()["created"] is False
        assert again.json()["id"] == body["id"]

    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        member = await db.get(Member, ctx["member_id"])
        assert member is not None
        assert member.email is None
        assert member.phone is None
        assert member.first_name == "ANON"
        assert member.last_name == member.member_number
        assert member.status == "ANONYMIZED"
        assert member.user_id is None
        invoice = await db.get(Invoice, ctx["invoice_id"])
        assert invoice is not None
        assert invoice.status == "PAID"
        assert invoice.total_amount_minor == 19900
        user = await db.get(User, ctx["user_id"])
        assert user is not None
        assert user.is_active is False
        sessions = list(
            (
                await db.execute(
                    select(UserSession).where(UserSession.user_id == ctx["user_id"])
                )
            ).scalars().all()
        )
        assert sessions
        assert all(s.is_revoked for s in sessions)
