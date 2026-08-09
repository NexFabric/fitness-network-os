"""Phase 10 finance domain — real PostgreSQL service tests (amount_minor only)."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.finance import (
    BillingAccount,
    Invoice,
    InvoiceStatus,
    PaymentStatus,
    ReconciliationItemStatus,
)
from app.models.member import Member
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.services.finance import FinanceService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Fin Org", domain=f"fin-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="Fin Tenant",
        organization_id=org.id,
        location_code=f"LOC-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


@pytest_asyncio.fixture
async def member(db_session: AsyncSession, tenant: Tenant) -> Member:
    m = Member(
        id=uuid4(),
        tenant_id=tenant.id,
        member_number=f"M-{uuid4().hex[:6]}",
        first_name="Pay",
        last_name="User",
        email=f"pay-{uuid4()}@example.com",
    )
    db_session.add(m)
    await db_session.commit()
    return m


@pytest.mark.asyncio
async def test_billing_account_and_invoice_with_discount(db_session, tenant, member):
    svc = FinanceService(db_session)
    account = await svc.get_or_create_billing_account(
        tenant.id, member_id=member.id, currency="TRY"
    )
    disc = await svc.create_discount(
        tenant.id, code="WELCOME10", name="Welcome", percent_bps=1000
    )
    inv = await svc.create_invoice(
        tenant.id,
        account.id,
        items=[
            {
                "description": "Monthly plan",
                "unit_amount_minor": 10000,
                "quantity": 1,
            }
        ],
        discount_code=disc.code,
        issue=True,
    )
    await db_session.commit()

    assert inv.status == InvoiceStatus.OPEN.value
    assert inv.total_amount_minor == 9000  # 10% off
    assert inv.discount_amount_minor == 1000
    assert inv.paid_amount_minor == 0
    assert inv.invoice_number is not None
    assert isinstance(inv.total_amount_minor, int)


@pytest.mark.asyncio
async def test_partial_payment_and_full_pay(db_session, tenant, member):
    svc = FinanceService(db_session)
    account = await svc.get_or_create_billing_account(tenant.id, member_id=member.id)
    inv = await svc.create_invoice(
        tenant.id,
        account.id,
        items=[{"description": "Fees", "unit_amount_minor": 100050, "quantity": 1}],
        issue=True,
    )
    p1 = await svc.record_payment(
        tenant.id,
        account.id,
        50025,
        "CASH",
        allocations=[{"invoice_id": inv.id, "amount_minor": 50025}],
        idempotency_key="pay-partial-1",
    )
    await db_session.refresh(inv)
    assert inv.status == InvoiceStatus.PARTIALLY_PAID.value
    assert inv.paid_amount_minor == 50025
    assert p1.amount_minor == 50025

    p2 = await svc.record_payment(
        tenant.id,
        account.id,
        50025,
        "TRANSFER",
        allocations=[{"invoice_id": inv.id, "amount_minor": 50025}],
        idempotency_key="pay-partial-2",
    )
    await db_session.refresh(inv)
    assert inv.status == InvoiceStatus.PAID.value
    assert inv.paid_amount_minor == 100050
    assert p2.status == PaymentStatus.SUCCEEDED.value
    await db_session.commit()


@pytest.mark.asyncio
async def test_payment_idempotent_replay(db_session, tenant, member):
    svc = FinanceService(db_session)
    account = await svc.get_or_create_billing_account(tenant.id, member_id=member.id)
    inv = await svc.create_invoice(
        tenant.id,
        account.id,
        items=[{"description": "X", "unit_amount_minor": 1000, "quantity": 1}],
        issue=True,
    )
    p1 = await svc.record_payment(
        tenant.id,
        account.id,
        1000,
        "CASH",
        allocations=[{"invoice_id": inv.id, "amount_minor": 1000}],
        idempotency_key="same-pay-key",
    )
    p2 = await svc.record_payment(
        tenant.id,
        account.id,
        1000,
        "CASH",
        allocations=[{"invoice_id": inv.id, "amount_minor": 1000}],
        idempotency_key="same-pay-key",
    )
    assert p1.id == p2.id
    await db_session.refresh(inv)
    assert inv.paid_amount_minor == 1000
    await db_session.commit()


@pytest.mark.asyncio
async def test_over_allocation_rejected(db_session, tenant, member):
    svc = FinanceService(db_session)
    account = await svc.get_or_create_billing_account(tenant.id, member_id=member.id)
    inv = await svc.create_invoice(
        tenant.id,
        account.id,
        items=[{"description": "X", "unit_amount_minor": 1000, "quantity": 1}],
        issue=True,
    )
    with pytest.raises(ValueError, match="exceeds invoice remaining"):
        await svc.record_payment(
            tenant.id,
            account.id,
            2000,
            "CASH",
            allocations=[{"invoice_id": inv.id, "amount_minor": 2000}],
            idempotency_key="over-alloc",
        )


@pytest.mark.asyncio
async def test_refund_partial_unwinds_invoice(db_session, tenant, member):
    svc = FinanceService(db_session)
    account = await svc.get_or_create_billing_account(tenant.id, member_id=member.id)
    inv = await svc.create_invoice(
        tenant.id,
        account.id,
        items=[{"description": "X", "unit_amount_minor": 5000, "quantity": 1}],
        issue=True,
    )
    pay = await svc.record_payment(
        tenant.id,
        account.id,
        5000,
        "CARD",
        allocations=[{"invoice_id": inv.id, "amount_minor": 5000}],
        idempotency_key="pay-for-refund",
    )
    await db_session.refresh(inv)
    assert inv.status == InvoiceStatus.PAID.value

    refund = await svc.refund_payment(
        tenant.id, pay.id, 2000, "refund-1", reason="partial"
    )
    await db_session.refresh(inv)
    await db_session.refresh(pay)
    assert refund.amount_minor == 2000
    assert pay.refunded_amount_minor == 2000
    assert pay.status == PaymentStatus.PARTIALLY_REFUNDED.value
    assert inv.paid_amount_minor == 3000
    assert inv.status == InvoiceStatus.PARTIALLY_PAID.value
    await db_session.commit()


@pytest.mark.asyncio
async def test_credit_apply_to_invoice(db_session, tenant, member):
    svc = FinanceService(db_session)
    account = await svc.get_or_create_billing_account(tenant.id, member_id=member.id)
    inv = await svc.create_invoice(
        tenant.id,
        account.id,
        items=[{"description": "X", "unit_amount_minor": 4000, "quantity": 1}],
        issue=True,
    )
    credit = await svc.issue_credit(
        tenant.id, account.id, 1500, "credit-1", reason="goodwill"
    )
    await svc.apply_credit_to_invoice(tenant.id, credit.id, inv.id, 1500)
    await db_session.refresh(inv)
    await db_session.refresh(credit)
    assert inv.paid_amount_minor == 1500
    assert inv.status == InvoiceStatus.PARTIALLY_PAID.value
    assert credit.remaining_minor == 0
    await db_session.commit()


@pytest.mark.asyncio
async def test_void_invoice_without_payments(db_session, tenant, member):
    svc = FinanceService(db_session)
    account = await svc.get_or_create_billing_account(tenant.id, member_id=member.id)
    inv = await svc.create_invoice(
        tenant.id,
        account.id,
        items=[{"description": "X", "unit_amount_minor": 100, "quantity": 1}],
        issue=True,
    )
    voided = await svc.void_invoice(tenant.id, inv.id)
    assert voided.status == InvoiceStatus.VOID.value
    await db_session.commit()


@pytest.mark.asyncio
async def test_reconciliation_match(db_session, tenant, member):
    svc = FinanceService(db_session)
    account = await svc.get_or_create_billing_account(tenant.id, member_id=member.id)
    inv = await svc.create_invoice(
        tenant.id,
        account.id,
        items=[{"description": "X", "unit_amount_minor": 2500, "quantity": 1}],
        issue=True,
    )
    pay = await svc.record_payment(
        tenant.id,
        account.id,
        2500,
        "TRANSFER",
        allocations=[{"invoice_id": inv.id, "amount_minor": 2500}],
        idempotency_key="recon-pay",
        provider_ref="BANK-1",
    )
    run = await svc.start_reconciliation(
        tenant.id,
        [{"external_ref": "BANK-1", "amount_minor": 2500, "currency": "TRY"}],
    )
    from app.models.finance import ReconciliationItem

    ri = (
        await db_session.execute(
            select(ReconciliationItem).where(ReconciliationItem.run_id == run.id)
        )
    ).scalars().first()
    assert ri is not None
    matched = await svc.match_reconciliation_item(tenant.id, ri.id, pay.id)
    assert matched.status == ReconciliationItemStatus.MATCHED.value
    completed = await svc.complete_reconciliation(tenant.id, run.id)
    assert completed.status == "COMPLETED"
    await db_session.commit()


@pytest.mark.asyncio
async def test_no_float_amounts(db_session, tenant, member):
    svc = FinanceService(db_session)
    account = await svc.get_or_create_billing_account(tenant.id, member_id=member.id)
    with pytest.raises(TypeError):
        await svc.record_payment(
            tenant.id,
            account.id,
            10.5,  # type: ignore[arg-type]
            "CASH",
            idempotency_key="float-bad",
        )


@pytest.mark.asyncio
async def test_finance_rls_isolation(
    pg_engine, pg_session_maker, db_session, tenant, member
):
    svc = FinanceService(db_session)
    account = await svc.get_or_create_billing_account(tenant.id, member_id=member.id)
    await svc.create_invoice(
        tenant.id,
        account.id,
        items=[{"description": "X", "unit_amount_minor": 100, "quantity": 1}],
        issue=True,
    )
    await db_session.commit()

    # other tenant
    org2 = Organization(name="Other", domain=f"o-{uuid4()}.com")
    db_session.add(org2)
    await db_session.flush()
    t2 = Tenant(
        id=uuid4(),
        name="T2",
        organization_id=org2.id,
        location_code=f"L-{uuid4().hex[:4]}",
    )
    db_session.add(t2)
    await db_session.commit()

    async with pg_session_maker() as session:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(t2.id)},
        )
        rows = (await session.execute(select(BillingAccount))).scalars().all()
        assert all(r.tenant_id == t2.id for r in rows)
        assert not any(r.tenant_id == tenant.id for r in rows)

        inv_rows = (await session.execute(select(Invoice))).scalars().all()
        assert all(r.tenant_id != tenant.id for r in inv_rows)
