"""NotificationBridge — domain → notification.requested path (real PG)."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.event_types import MEMBERSHIP_ACTIVATED_V1, NOTIFICATION_REQUESTED_V1
from app.models.notification import DELIVERY_QUEUED, NotificationDelivery
from app.models.organization import Organization
from app.models.outbox import OutboxEvent
from app.models.rbac import Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User
from app.services.notification import NotificationService
from app.services.notification_bridge import NotificationBridge


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Bridge Org", domain=f"bridge-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="Bridge Tenant",
        organization_id=org.id,
        location_code=f"B-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


async def _tenant_user(db: AsyncSession, tenant_id) -> User:
    user = User(
        email=f"member-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    role = Role(name=f"member-{uuid4().hex[:8]}", description="t", is_system=False)
    db.add(role)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant_id))
    await db.commit()
    return user


@pytest.mark.asyncio
async def test_schedule_for_member_user_enqueues_notification_requested(
    db_session, tenant
):
    user = await _tenant_user(db_session, tenant.id)
    svc = NotificationService(db_session)
    await svc.create_template(
        tenant.id,
        code="membership_activated",
        name="Membership activated",
        channel="EMAIL",
        subject_template="Welcome $first_name",
        body_template="Hi $first_name, your membership is active at $gym_name.",
    )
    await db_session.commit()

    bridge = NotificationBridge(db_session)
    membership_id = uuid4()
    domain_event_id = str(uuid4())
    result = await bridge.schedule_for_member_user(
        tenant.id,
        user.id,
        template_code="membership_activated",
        channel="EMAIL",
        context={"first_name": "Ada", "gym_name": "GymClub"},
        dedupe_key=f"membership.activated:{membership_id}",
        correlation_id=f"corr-{membership_id}",
        source_event_type=MEMBERSHIP_ACTIVATED_V1,
        source_event_id=domain_event_id,
        enqueue_outbox=True,
    )
    await db_session.commit()

    assert result.created is True
    d = result.delivery
    assert d.recipient_user_id == user.id
    assert d.status == DELIVERY_QUEUED
    assert d.subject == "Welcome Ada"
    assert "GymClub" in (d.body or "")
    assert d.source_event_type == MEMBERSHIP_ACTIVATED_V1
    assert d.source_event_id == domain_event_id
    assert d.dedupe_key == f"membership.activated:{membership_id}"
    assert result.outbox_event_id is not None

    outbox_row = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.id == result.outbox_event_id)
        )
    ).scalars().first()
    assert outbox_row is not None
    assert outbox_row.event_type == NOTIFICATION_REQUESTED_V1
    assert outbox_row.tenant_id == tenant.id
    assert str(d.id) in str(outbox_row.payload)


@pytest.mark.asyncio
async def test_schedule_from_domain_event_idempotent_dedupe(db_session, tenant):
    user = await _tenant_user(db_session, tenant.id)
    svc = NotificationService(db_session)
    await svc.create_template(
        tenant.id,
        code="membership_activated",
        name="Membership activated",
        channel="EMAIL",
        body_template="active",
    )
    await db_session.commit()

    bridge = NotificationBridge(db_session)
    key = f"membership.activated:{uuid4()}"
    a = await bridge.schedule_from_domain_event(
        tenant.id,
        event_type=MEMBERSHIP_ACTIVATED_V1,
        event_id=str(uuid4()),
        user_id=user.id,
        template_code="membership_activated",
        channel="EMAIL",
        context={},
        dedupe_key=key,
        enqueue_outbox=True,
    )
    await db_session.commit()
    b = await bridge.schedule_from_domain_event(
        tenant.id,
        event_type=MEMBERSHIP_ACTIVATED_V1,
        event_id=str(uuid4()),
        user_id=user.id,
        template_code="membership_activated",
        channel="EMAIL",
        context={},
        dedupe_key=key,
        enqueue_outbox=True,
    )
    await db_session.commit()

    assert a.created is True
    assert b.created is False
    assert a.delivery.id == b.delivery.id

    # Only one delivery for the dedupe key
    rows = (
        await db_session.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.tenant_id == tenant.id,
                NotificationDelivery.dedupe_key == key,
            )
        )
    ).scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_schedule_for_member_user_rejects_foreign_user(db_session, tenant):
    foreign = User(
        email=f"foreign-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db_session.add(foreign)
    await db_session.commit()

    svc = NotificationService(db_session)
    await svc.create_template(
        tenant.id,
        code="ping",
        name="Ping",
        channel="EMAIL",
        body_template="x",
    )
    await db_session.commit()

    bridge = NotificationBridge(db_session)
    with pytest.raises(ValueError, match="recipient_not_in_tenant"):
        await bridge.schedule_for_member_user(
            tenant.id,
            foreign.id,
            template_code="ping",
            channel="EMAIL",
            enqueue_outbox=False,
        )


@pytest.mark.asyncio
async def test_schedule_for_member_user_requires_template_code(db_session, tenant):
    user = await _tenant_user(db_session, tenant.id)
    bridge = NotificationBridge(db_session)
    with pytest.raises(ValueError, match="template_code_required"):
        await bridge.schedule_for_member_user(
            tenant.id,
            user.id,
            template_code="  ",
            channel="EMAIL",
            enqueue_outbox=False,
        )
