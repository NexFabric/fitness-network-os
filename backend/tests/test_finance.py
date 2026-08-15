from uuid import uuid4

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from app.api.deps import current_tenant_id_var
from app.db.base import Base
from app.models.finance import (
    BillingAccount,
    Invoice,
    InvoiceItem,
    Payment,
    PaymentAllocation,
)
from app.models.member import Member


@pytest.fixture
async def finance_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(Session, "after_begin")
    def mock_set_tenant_id(session, transaction, connection):
        pass

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def finance_session_maker(finance_engine):
    return async_sessionmaker(
        finance_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.mark.asyncio
async def test_finance_tenant_isolation(finance_session_maker):
    tenant_id = uuid4()
    token = current_tenant_id_var.set(tenant_id)

    async with finance_session_maker() as session:
        member = Member(
            tenant_id=tenant_id,
            member_number="M-FIN-001",
            first_name="Finance",
            last_name="Test",
        )
        session.add(member)
        await session.commit()

        account = BillingAccount(tenant_id=tenant_id, member_id=member.id)
        session.add(account)
        await session.commit()

        invoice = Invoice(
            tenant_id=tenant_id,
            billing_account_id=account.id,
            total_amount_minor=15000,  # 150.00
            currency="TRY",
            status="OPEN",
        )
        session.add(invoice)
        await session.commit()

        item = InvoiceItem(
            tenant_id=tenant_id,
            invoice_id=invoice.id,
            description="Monthly Membership",
            unit_amount_minor=15000,
            amount_minor=15000,
            quantity=1,
        )
        session.add(item)
        await session.commit()

        # Verify tenant_id correctly assigned
        result = await session.execute(select(Invoice).filter_by(tenant_id=tenant_id))
        inv_db = result.scalars().first()
        assert inv_db.total_amount_minor == 15000
        assert inv_db.currency == "TRY"
        assert inv_db.tenant_id == tenant_id

    current_tenant_id_var.reset(token)


@pytest.mark.asyncio
async def test_payment_allocation_math(finance_session_maker):
    tenant_id = uuid4()
    token = current_tenant_id_var.set(tenant_id)

    async with finance_session_maker() as session:
        account = BillingAccount(tenant_id=tenant_id)
        session.add(account)
        await session.commit()

        # Invoice for 1000.50 TRY (100050 minor)
        invoice = Invoice(
            tenant_id=tenant_id,
            billing_account_id=account.id,
            total_amount_minor=100050,
            currency="TRY",
            status="OPEN",
        )
        session.add(invoice)

        # Payment for 500.25 TRY (50025 minor)
        payment = Payment(
            tenant_id=tenant_id,
            billing_account_id=account.id,
            amount_minor=50025,
            currency="TRY",
            status="SUCCEEDED",
            method="CREDIT_CARD",
        )
        session.add(payment)
        await session.commit()

        # Partial allocation
        allocation = PaymentAllocation(
            tenant_id=tenant_id,
            payment_id=payment.id,
            invoice_id=invoice.id,
            amount_minor=50025,
        )
        session.add(allocation)
        await session.commit()

        # Calculate remaining
        result = await session.execute(select(Invoice).filter_by(id=invoice.id))
        inv_db = result.scalars().first()

        alloc_result = await session.execute(
            select(PaymentAllocation).filter_by(invoice_id=invoice.id)
        )
        allocations = alloc_result.scalars().all()

        total_allocated = sum(a.amount_minor for a in allocations)
        remaining = inv_db.total_amount_minor - total_allocated

        # 100050 - 50025 = 50025
        assert isinstance(total_allocated, int)
        assert isinstance(remaining, int)
        assert total_allocated == 50025
        assert remaining == 50025
        assert remaining + total_allocated == inv_db.total_amount_minor

    current_tenant_id_var.reset(token)
