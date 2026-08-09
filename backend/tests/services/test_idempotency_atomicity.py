"""Phase 15.5 — idempotency failure atomicity + FAILED hash binding."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.idempotency_uow import run_idempotent
from app.models.idempotency import IdempotencyRecord, IdempotencyStatus
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.services.idempotency import IdempotencyOutcome, IdempotencyService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Idem Atom", domain=f"ia-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="Idem Atom T",
        organization_id=org.id,
        location_code=f"IA-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


@pytest.mark.asyncio
async def test_business_failure_rolls_back_partial_flush(db_session, tenant):
    """Domain flush inside business must not survive after UoW failure."""
    side_domain = f"side-{uuid4().hex}.com"

    async def business():
        org = Organization(name="ShouldRollback", domain=side_domain)
        db_session.add(org)
        await db_session.flush()
        raise RuntimeError("boom after flush")

    with pytest.raises(RuntimeError, match="boom"):
        await run_idempotent(
            db_session,
            tenant_id=tenant.id,
            operation="test.atomic",
            key=f"k-{uuid4().hex}",
            request_payload={"a": 1},
            business=business,
        )

    leaked = (
        await db_session.execute(
            select(Organization).where(Organization.domain == side_domain)
        )
    ).scalar_one_or_none()
    assert leaked is None

    rec = (
        await db_session.execute(
            select(IdempotencyRecord).where(
                IdempotencyRecord.tenant_id == tenant.id,
                IdempotencyRecord.operation == "test.atomic",
            )
        )
    ).scalar_one()
    assert rec.status == IdempotencyStatus.FAILED.value


@pytest.mark.asyncio
async def test_failed_same_hash_retry_different_hash_conflict(db_session, tenant):
    svc = IdempotencyService
    key = f"k-{uuid4().hex}"
    h1 = svc.canonical_request_hash({"x": 1})
    h2 = svc.canonical_request_hash({"x": 2})
    owner = uuid4().hex

    begin = await svc.begin(
        db_session, tenant.id, "test.fail", key, h1, owner_token=owner
    )
    assert begin.outcome == IdempotencyOutcome.PROCEED
    await svc.fail(db_session, begin.record, owner_token=owner, response_status=500)
    await db_session.commit()

    r_bad = await svc.begin(
        db_session, tenant.id, "test.fail", key, h2, owner_token=uuid4().hex
    )
    assert r_bad.outcome == IdempotencyOutcome.CONFLICT

    r_ok = await svc.begin(
        db_session, tenant.id, "test.fail", key, h1, owner_token=uuid4().hex
    )
    assert r_ok.outcome == IdempotencyOutcome.PROCEED
    await db_session.commit()
