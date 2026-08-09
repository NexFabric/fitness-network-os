"""Phase 12 IdempotencyService — real PostgreSQL tests."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.organization import Organization
from app.models.tenant import Tenant
from app.services.idempotency import (
    FINANCE_PAYMENT_CREATE,
    IdempotencyOutcome,
    IdempotencyService,
)


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Idem Org", domain=f"idem-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="Idem Tenant",
        organization_id=org.id,
        location_code=f"LOC-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


@pytest.mark.asyncio
async def test_first_claim_proceeds(db_session, tenant):
    h = IdempotencyService.canonical_request_hash({"a": 1})
    r = await IdempotencyService.begin(
        db_session,
        tenant.id,
        FINANCE_PAYMENT_CREATE,
        "key-1",
        h,
        owner_token="owner-a",
    )
    assert r.outcome == IdempotencyOutcome.PROCEED
    assert r.record is not None
    await db_session.commit()


@pytest.mark.asyncio
async def test_replay_same_hash_returns_cached(db_session, tenant):
    h = IdempotencyService.canonical_request_hash({"amount": 100})
    b1 = await IdempotencyService.begin(
        db_session,
        tenant.id,
        FINANCE_PAYMENT_CREATE,
        "key-replay",
        h,
        owner_token="o1",
    )
    assert b1.outcome == IdempotencyOutcome.PROCEED
    await IdempotencyService.complete(
        db_session,
        b1.record,
        owner_token="o1",
        response_status=200,
        response_body={"ok": True, "id": "x"},
    )
    await db_session.commit()

    b2 = await IdempotencyService.begin(
        db_session,
        tenant.id,
        FINANCE_PAYMENT_CREATE,
        "key-replay",
        h,
        owner_token="o2",
    )
    assert b2.outcome == IdempotencyOutcome.REPLAY
    assert b2.response_body == {"ok": True, "id": "x"}
    assert b2.response_status == 200
    await db_session.commit()


@pytest.mark.asyncio
async def test_conflict_different_hash(db_session, tenant):
    h1 = IdempotencyService.canonical_request_hash({"amount": 100})
    h2 = IdempotencyService.canonical_request_hash({"amount": 200})
    b1 = await IdempotencyService.begin(
        db_session,
        tenant.id,
        FINANCE_PAYMENT_CREATE,
        "key-conflict",
        h1,
        owner_token="o1",
    )
    await IdempotencyService.complete(
        db_session,
        b1.record,
        owner_token="o1",
        response_status=200,
        response_body={"ok": True},
    )
    await db_session.commit()

    b2 = await IdempotencyService.begin(
        db_session,
        tenant.id,
        FINANCE_PAYMENT_CREATE,
        "key-conflict",
        h2,
        owner_token="o2",
    )
    assert b2.outcome == IdempotencyOutcome.CONFLICT
    await db_session.commit()


@pytest.mark.asyncio
async def test_in_progress_while_lease_active(db_session, tenant):
    h = IdempotencyService.canonical_request_hash({"x": 1})
    b1 = await IdempotencyService.begin(
        db_session,
        tenant.id,
        FINANCE_PAYMENT_CREATE,
        "key-lease",
        h,
        owner_token="o1",
        lease_seconds=60,
    )
    assert b1.outcome == IdempotencyOutcome.PROCEED
    await db_session.commit()

    b2 = await IdempotencyService.begin(
        db_session,
        tenant.id,
        FINANCE_PAYMENT_CREATE,
        "key-lease",
        h,
        owner_token="o2",
        lease_seconds=60,
    )
    assert b2.outcome == IdempotencyOutcome.IN_PROGRESS
    assert b2.retry_after_seconds is not None and b2.retry_after_seconds >= 1
    await db_session.commit()


@pytest.mark.asyncio
async def test_reclaim_expired_lease(db_session, tenant):
    h = IdempotencyService.canonical_request_hash({"y": 2})
    b1 = await IdempotencyService.begin(
        db_session,
        tenant.id,
        FINANCE_PAYMENT_CREATE,
        "key-reclaim",
        h,
        owner_token="o1",
        lease_seconds=0,
    )
    assert b1.outcome == IdempotencyOutcome.PROCEED
    # Force lease into the past
    from datetime import UTC, datetime, timedelta

    b1.record.locked_until = datetime.now(UTC) - timedelta(seconds=5)
    await db_session.flush()
    await db_session.commit()

    b2 = await IdempotencyService.begin(
        db_session,
        tenant.id,
        FINANCE_PAYMENT_CREATE,
        "key-reclaim",
        h,
        owner_token="o2",
        lease_seconds=30,
    )
    assert b2.outcome == IdempotencyOutcome.PROCEED
    assert b2.record is not None
    assert b2.record.owner_token == "o2"
    await db_session.commit()


@pytest.mark.asyncio
async def test_cross_tenant_same_key_independent(db_session, tenant):
    org2 = Organization(name="Other", domain=f"o2-{uuid4()}.com")
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

    h = IdempotencyService.canonical_request_hash({"z": 1})
    b1 = await IdempotencyService.begin(
        db_session,
        tenant.id,
        FINANCE_PAYMENT_CREATE,
        "shared-key",
        h,
        owner_token="a",
    )
    b2 = await IdempotencyService.begin(
        db_session,
        t2.id,
        FINANCE_PAYMENT_CREATE,
        "shared-key",
        h,
        owner_token="b",
    )
    assert b1.outcome == IdempotencyOutcome.PROCEED
    assert b2.outcome == IdempotencyOutcome.PROCEED
    await db_session.commit()


@pytest.mark.asyncio
async def test_concurrent_same_key_single_proceed(pg_engine, tenant):
    """Two sessions race; only one PROCEED without completed result; other IN_PROGRESS or REPLAY after."""
    import asyncio

    h = IdempotencyService.canonical_request_hash({"race": True})
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)

    async def claim(token: str):
        async with maker() as session:
            res = await IdempotencyService.begin(
                session,
                tenant.id,
                FINANCE_PAYMENT_CREATE,
                "race-key",
                h,
                owner_token=token,
                lease_seconds=60,
            )
            await session.commit()
            return res.outcome

    o1, o2 = await asyncio.gather(claim("t1"), claim("t2"))
    outcomes = {o1, o2}
    assert IdempotencyOutcome.PROCEED in outcomes
    assert outcomes <= {
        IdempotencyOutcome.PROCEED,
        IdempotencyOutcome.IN_PROGRESS,
    }
    # Exactly one PROCEED
    assert [o1, o2].count(IdempotencyOutcome.PROCEED) == 1
