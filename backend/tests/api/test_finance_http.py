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

    reissue = await api_client.post(
        f"/api/v1/finance/invoices/{invoice_id}/issue",
        headers=headers,
    )
    assert reissue.status_code == 400

    missing_void = await api_client.post(
        f"/api/v1/finance/invoices/{uuid4()}/void",
        headers=headers,
    )
    assert missing_void.status_code == 400


async def _finance_world(pg_engine):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Fin Depth Org", domain=f"fnd-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Fin Depth T",
            organization_id=org.id,
            location_code=f"FD-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()
        member = Member(
            id=uuid4(),
            tenant_id=tenant.id,
            member_number=f"M-{uuid4().hex[:6]}",
            first_name="Depth",
            last_name="Pay",
            email=f"depth-{uuid4().hex[:6]}@example.com",
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
        reader, reader_token = await _user_with_role(
            db, tenant_id=tenant.id, perm_names=["finance:read"]
        )
        await db.commit()
        return {
            "tenant_id": tenant.id,
            "member_id": member.id,
            "token": token,
            "reader_token": reader_token,
            "user_id": _user.id,
            "reader_id": reader.id,
        }


def _fin_headers(token: str, tenant_id, **extra) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
        **extra,
    }


@pytest.mark.asyncio
async def test_finance_http_issue_void_credit_refund_and_reconcile(
    api_client, pg_engine
):
    from app.models.finance import ReconciliationItem

    ctx = await _finance_world(pg_engine)
    headers = _fin_headers(ctx["token"], ctx["tenant_id"])

    missing_party = await api_client.post(
        "/api/v1/finance/billing-accounts",
        headers=headers,
        json={"currency": "TRY"},
    )
    assert missing_party.status_code == 400

    account_res = await api_client.post(
        "/api/v1/finance/billing-accounts",
        headers=headers,
        json={"member_id": str(ctx["member_id"]), "currency": "TRY"},
    )
    assert account_res.status_code == 200, account_res.text
    account_id = account_res.json()["id"]

    unknown_inv = await api_client.post(
        "/api/v1/finance/invoices",
        headers=headers,
        json={
            "billing_account_id": str(uuid4()),
            "items": [{"description": "X", "unit_amount_minor": 100, "quantity": 1}],
        },
    )
    assert unknown_inv.status_code == 400

    empty_items = await api_client.post(
        "/api/v1/finance/invoices",
        headers=headers,
        json={"billing_account_id": account_id, "items": []},
    )
    assert empty_items.status_code == 400

    idem_key = f"inv-{uuid4().hex}"
    draft = await api_client.post(
        "/api/v1/finance/invoices",
        headers=_fin_headers(
            ctx["token"], ctx["tenant_id"], **{"Idempotency-Key": idem_key}
        ),
        json={
            "billing_account_id": account_id,
            "items": [
                {"description": "Draft month", "unit_amount_minor": 8000, "quantity": 1}
            ],
            "issue": False,
        },
    )
    assert draft.status_code == 200, draft.text
    draft_id = draft.json()["id"]
    assert draft.json()["status"] == "DRAFT"
    replay = await api_client.post(
        "/api/v1/finance/invoices",
        headers=_fin_headers(
            ctx["token"], ctx["tenant_id"], **{"Idempotency-Key": idem_key}
        ),
        json={
            "billing_account_id": account_id,
            "items": [
                {"description": "Draft month", "unit_amount_minor": 8000, "quantity": 1}
            ],
            "issue": False,
        },
    )
    assert replay.status_code == 200
    assert replay.json()["id"] == draft_id

    issued = await api_client.post(
        f"/api/v1/finance/invoices/{draft_id}/issue", headers=headers
    )
    assert issued.status_code == 200, issued.text
    assert issued.json()["status"] == "OPEN"
    assert issued.json()["invoice_number"]

    voided = await api_client.post(
        f"/api/v1/finance/invoices/{draft_id}/void", headers=headers
    )
    assert voided.status_code == 200, voided.text
    assert voided.json()["status"] == "VOID"

    pay_inv = await api_client.post(
        "/api/v1/finance/invoices",
        headers=headers,
        json={
            "billing_account_id": account_id,
            "items": [
                {"description": "Payable", "unit_amount_minor": 5000, "quantity": 1}
            ],
            "issue": True,
        },
    )
    assert pay_inv.status_code == 200, pay_inv.text
    payable_id = pay_inv.json()["id"]

    credit_inv = await api_client.post(
        "/api/v1/finance/invoices",
        headers=headers,
        json={
            "billing_account_id": account_id,
            "items": [
                {
                    "description": "Credit target",
                    "unit_amount_minor": 3000,
                    "quantity": 1,
                }
            ],
            "issue": True,
        },
    )
    assert credit_inv.status_code == 200, credit_inv.text
    credit_invoice_id = credit_inv.json()["id"]

    missing_refund_key = await api_client.post(
        f"/api/v1/finance/payments/{uuid4()}/refunds",
        headers=headers,
        json={"amount_minor": 100},
    )
    assert missing_refund_key.status_code == 400

    pay_key = f"pay-{uuid4().hex}"
    pay_res = await api_client.post(
        "/api/v1/finance/payments",
        headers=_fin_headers(
            ctx["token"], ctx["tenant_id"], **{"Idempotency-Key": pay_key}
        ),
        json={
            "billing_account_id": account_id,
            "amount_minor": 5000,
            "method": "CASH",
            "allocations": [{"invoice_id": payable_id, "amount_minor": 5000}],
        },
    )
    assert pay_res.status_code == 200, pay_res.text
    payment_id = pay_res.json()["id"]

    refund_key = f"ref-{uuid4().hex}"
    refund = await api_client.post(
        f"/api/v1/finance/payments/{payment_id}/refunds",
        headers=_fin_headers(
            ctx["token"], ctx["tenant_id"], **{"Idempotency-Key": refund_key}
        ),
        json={"amount_minor": 2000, "reason": "partial"},
    )
    assert refund.status_code == 200, refund.text
    assert refund.json()["amount_minor"] == 2000
    refund_again = await api_client.post(
        f"/api/v1/finance/payments/{payment_id}/refunds",
        headers=_fin_headers(
            ctx["token"], ctx["tenant_id"], **{"Idempotency-Key": refund_key}
        ),
        json={"amount_minor": 2000, "reason": "partial"},
    )
    assert refund_again.status_code == 200
    assert refund_again.json()["id"] == refund.json()["id"]

    missing_credit_key = await api_client.post(
        "/api/v1/finance/credits",
        headers=headers,
        json={"billing_account_id": account_id, "amount_minor": 3000},
    )
    assert missing_credit_key.status_code == 400

    credit_key = f"cr-{uuid4().hex}"
    credit = await api_client.post(
        "/api/v1/finance/credits",
        headers=_fin_headers(
            ctx["token"], ctx["tenant_id"], **{"Idempotency-Key": credit_key}
        ),
        json={
            "billing_account_id": account_id,
            "amount_minor": 3000,
            "reason": "goodwill",
        },
    )
    assert credit.status_code == 200, credit.text
    credit_id = credit.json()["id"]
    credit_replay = await api_client.post(
        "/api/v1/finance/credits",
        headers=_fin_headers(
            ctx["token"], ctx["tenant_id"], **{"Idempotency-Key": credit_key}
        ),
        json={
            "billing_account_id": account_id,
            "amount_minor": 3000,
            "reason": "goodwill",
        },
    )
    assert credit_replay.json()["id"] == credit_id

    applied = await api_client.post(
        f"/api/v1/finance/credits/{credit_id}/apply",
        headers=headers,
        json={"invoice_id": credit_invoice_id, "amount_minor": 3000},
    )
    assert applied.status_code == 200, applied.text
    assert applied.json()["amount_minor"] == 3000

    apply_missing = await api_client.post(
        f"/api/v1/finance/credits/{uuid4()}/apply",
        headers=headers,
        json={"invoice_id": credit_invoice_id, "amount_minor": 100},
    )
    assert apply_missing.status_code == 400

    empty_recon = await api_client.post(
        "/api/v1/finance/reconciliations",
        headers=headers,
        json={"items": []},
    )
    assert empty_recon.status_code == 400

    recon = await api_client.post(
        "/api/v1/finance/reconciliations",
        headers=headers,
        json={
            "items": [
                {"external_ref": "BANK-1", "amount_minor": 5000, "currency": "TRY"}
            ],
            "notes": "august",
        },
    )
    assert recon.status_code == 200, recon.text
    run_id = recon.json()["id"]
    assert recon.json()["status"] == "OPEN"

    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        item = (
            await db.execute(
                select(ReconciliationItem).where(
                    ReconciliationItem.tenant_id == ctx["tenant_id"]
                )
            )
        ).scalar_one()
        item_id = item.id

    matched = await api_client.post(
        f"/api/v1/finance/reconciliations/items/{item_id}/match",
        headers=headers,
        json={"payment_id": payment_id},
    )
    assert matched.status_code == 200, matched.text
    assert matched.json()["status"] == "MATCHED"
    assert matched.json()["matched_payment_id"] == payment_id

    match_missing = await api_client.post(
        f"/api/v1/finance/reconciliations/items/{uuid4()}/match",
        headers=headers,
        json={"payment_id": payment_id},
    )
    assert match_missing.status_code == 400

    completed = await api_client.post(
        f"/api/v1/finance/reconciliations/{run_id}/complete", headers=headers
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "COMPLETED"
    assert completed.json()["completed_at"] is not None

    complete_missing = await api_client.post(
        f"/api/v1/finance/reconciliations/{uuid4()}/complete", headers=headers
    )
    assert complete_missing.status_code == 400

    listed_member = await api_client.get(
        "/api/v1/finance/invoices",
        headers=headers,
        params={"member_id": str(ctx["member_id"])},
    )
    assert listed_member.status_code == 200
    assert listed_member.json()["total"] >= 1

    pays_member = await api_client.get(
        "/api/v1/finance/payments",
        headers=headers,
        params={"member_id": str(ctx["member_id"])},
    )
    assert pays_member.status_code == 200
    assert pays_member.json()["total"] >= 1

    neither_discount = await api_client.post(
        "/api/v1/finance/discounts",
        headers=headers,
        json={"code": "NONE", "name": "none"},
    )
    assert neither_discount.status_code == 400

    both_discount = await api_client.post(
        "/api/v1/finance/discounts",
        headers=headers,
        json={
            "code": "BOTH",
            "name": "both",
            "amount_minor": 100,
            "percent_bps": 1000,
        },
    )
    assert both_discount.status_code == 400

    reader_headers = _fin_headers(ctx["reader_token"], ctx["tenant_id"])
    denied_write = await api_client.post(
        "/api/v1/finance/billing-accounts",
        headers=reader_headers,
        json={"member_id": str(ctx["member_id"]), "currency": "TRY"},
    )
    assert denied_write.status_code == 403

    denied_refund = await api_client.post(
        f"/api/v1/finance/payments/{payment_id}/refunds",
        headers=_fin_headers(
            ctx["reader_token"], ctx["tenant_id"], **{"Idempotency-Key": "x"}
        ),
        json={"amount_minor": 100},
    )
    assert denied_refund.status_code == 403
