from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.finance import (
    BillingAccount,
    Invoice,
    InvoiceStatus,
    PaymentAttemptStatus,
)
from app.models.organization import Organization
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User
from app.services.finance import FinanceService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest.mark.asyncio
async def test_dunning_policy_lifecycle_and_attempts(db_session: AsyncSession):
    # 1. Setup org, tenant, user and billing account
    org = Organization(name="Dunning Org", domain=f"org-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()

    tenant = Tenant(
        id=uuid4(),
        organization_id=org.id,
        name="Dunning Test Gym",
        status=TenantStatus.ACTIVE.value,
        location_code="DNN-01",
    )
    db_session.add(tenant)
    await db_session.flush()

    service = FinanceService(db_session)
    policy = await service.get_or_create_dunning_policy(tenant.id)
    assert policy.tenant_id == tenant.id
    assert policy.max_retry_attempts == 3
    assert policy.grace_period_days == 3

    user = User(
        id=uuid4(),
        email=f"dunning_user_{uuid4()}@test.local",
        hashed_password="hash",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.flush()

    account = BillingAccount(
        id=uuid4(),
        tenant_id=tenant.id,
        user_id=user.id,
        currency="TRY",
    )
    db_session.add(account)
    await db_session.flush()

    # 2. Create invoice
    invoice = Invoice(
        id=uuid4(),
        tenant_id=tenant.id,
        billing_account_id=account.id,
        invoice_number="INV-DNN-001",
        status=InvoiceStatus.OPEN.value,
        currency="TRY",
        total_amount_minor=12000,
        paid_amount_minor=0,
        discount_amount_minor=0,
        due_date=datetime.now(UTC),
        retry_count=0,
    )
    db_session.add(invoice)
    await db_session.flush()

    # 3. Record failed payment attempts
    attempt1 = await service.record_payment_attempt(
        tenant_id=tenant.id,
        invoice_id=invoice.id,
        amount_minor=12000,
        status=PaymentAttemptStatus.FAILED,
        gateway_provider="mock_iyzico",
        error_code="INSUFFICIENT_FUNDS",
        error_message="Yetersiz bakiye",
    )
    assert attempt1.attempt_number == 1
    assert attempt1.status == "FAILED"
    assert invoice.retry_count == 1
    assert invoice.next_retry_at is not None
    assert invoice.status == InvoiceStatus.OPEN.value

    # Attempt 2
    attempt2 = await service.record_payment_attempt(
        tenant_id=tenant.id,
        invoice_id=invoice.id,
        amount_minor=12000,
        status=PaymentAttemptStatus.FAILED,
        gateway_provider="mock_iyzico",
        error_code="INSUFFICIENT_FUNDS",
    )
    assert attempt2.attempt_number == 2
    assert invoice.retry_count == 2
    assert invoice.status == InvoiceStatus.OPEN.value

    # Attempt 3 (reaches max_retry_attempts = 3) -> next_retry_at should be cleared (exhausted)
    attempt3 = await service.record_payment_attempt(
        tenant_id=tenant.id,
        invoice_id=invoice.id,
        amount_minor=12000,
        status=PaymentAttemptStatus.FAILED,
        gateway_provider="mock_iyzico",
        error_code="CARD_DECLINED",
    )
    assert attempt3.attempt_number == 3
    assert invoice.retry_count == 3
    assert invoice.next_retry_at is None

    # 4. List attempts
    attempts = await service.list_payment_attempts(tenant.id, invoice.id)
    assert len(attempts) == 3
    assert [a.attempt_number for a in attempts] == [1, 2, 3]
