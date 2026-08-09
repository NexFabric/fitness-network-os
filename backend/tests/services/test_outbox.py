"""Phase 15 outbox/inbox engine — real PostgreSQL tests."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.organization import Organization
from app.models.outbox import InboxEvent, OutboxEvent
from app.models.tenant import Tenant
from app.services.outbox import OutboxService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Outbox Org", domain=f"obx-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="Outbox Tenant",
        organization_id=org.id,
        location_code=f"O-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


@pytest.mark.asyncio
async def test_enqueue_and_publish(db_session, tenant):
    svc = OutboxService(db_session)
    r = await svc.enqueue(
        tenant.id,
        "membership.activated",
        {"membership_id": str(uuid4())},
        aggregate_type="membership",
    )
    await db_session.commit()
    assert r.created is True
    assert r.event.status == "PENDING"

    claimed = await svc.claim_pending(tenant_id=tenant.id, worker_id="w-pub")
    assert len(claimed) == 1
    assert claimed[0].status == "PROCESSING"
    await db_session.commit()

    async def pub(ev):
        assert ev.event_type == "membership.activated"

    stats = await svc.dispatch_claimed(claimed, pub, worker_id="w-pub")
    await db_session.commit()
    assert stats["published"] == 1

    row = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.id == claimed[0].id)
        )
    ).scalar_one()
    assert row.status == "PUBLISHED"
    assert row.processed_at is not None


@pytest.mark.asyncio
async def test_dedupe_key(db_session, tenant):
    svc = OutboxService(db_session)
    a = await svc.enqueue(
        tenant.id, "payment.captured", {"n": 1}, dedupe_key="pay-1"
    )
    await db_session.commit()
    b = await svc.enqueue(
        tenant.id, "payment.captured", {"n": 2}, dedupe_key="pay-1"
    )
    await db_session.commit()
    assert a.created is True
    assert b.created is False
    assert a.event.id == b.event.id


@pytest.mark.asyncio
async def test_inbox_exactly_once(db_session, tenant):
    svc = OutboxService(db_session)
    first = await svc.receive_inbox(
        tenant.id,
        event_id="wh_abc",
        event_type="stripe.payment_intent.succeeded",
        payload={"amount": 100},
    )
    await db_session.commit()
    assert first.is_duplicate is False

    second = await svc.receive_inbox(
        tenant.id,
        event_id="wh_abc",
        event_type="stripe.payment_intent.succeeded",
        payload={"amount": 100},
    )
    await db_session.commit()
    assert second.is_duplicate is True
    assert second.event.id == first.event.id

    handled: list[str] = []

    async def handler(db, ev: InboxEvent):
        handled.append(ev.event_id)

    stats = await svc.process_pending_inbox(
        tenant.id,
        {"stripe.payment_intent.succeeded": handler},
    )
    await db_session.commit()
    assert stats["processed"] == 1
    assert handled == ["wh_abc"]

    # No reprocess
    stats2 = await svc.process_pending_inbox(
        tenant.id,
        {"stripe.payment_intent.succeeded": handler},
    )
    await db_session.commit()
    assert stats2["processed"] == 0


@pytest.mark.asyncio
async def test_publish_failure_retries(db_session, tenant):
    svc = OutboxService(db_session)
    await svc.enqueue(tenant.id, "notify.email", {"to": "a@b.c"})
    await db_session.commit()
    claimed = await svc.claim_pending(tenant_id=tenant.id, worker_id="w-fail")
    await db_session.commit()

    async def boom(_ev):
        raise RuntimeError("smtp down")

    stats = await svc.dispatch_claimed(claimed, boom, worker_id="w-fail")
    await db_session.commit()
    assert stats["failed"] == 1
    row = (
        await db_session.execute(select(OutboxEvent).where(OutboxEvent.tenant_id == tenant.id))
    ).scalar_one()
    assert row.status == "FAILED"
    assert row.available_at is not None


@pytest.mark.asyncio
async def test_cross_tenant_inbox_same_event_id(db_session, tenant):
    org = Organization(name="Other", domain=f"ox-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t2 = Tenant(
        id=uuid4(),
        name="T2",
        organization_id=org.id,
        location_code=f"T2-{uuid4().hex[:4]}",
    )
    db_session.add(t2)
    await db_session.commit()

    svc = OutboxService(db_session)
    a = await svc.receive_inbox(
        tenant.id, event_id="same", event_type="x", payload={}
    )
    b = await svc.receive_inbox(
        t2.id, event_id="same", event_type="x", payload={}
    )
    await db_session.commit()
    assert a.is_duplicate is False
    assert b.is_duplicate is False
    assert a.event.id != b.event.id
