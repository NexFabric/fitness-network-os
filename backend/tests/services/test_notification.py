"""Phase 16 notification service — real PostgreSQL tests."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.event_types import NOTIFICATION_REQUESTED_V1
from app.models.notification import (
    DELIVERY_CANCELLED,
    DELIVERY_DEAD,
    DELIVERY_FAILED,
    DELIVERY_QUEUED,
    DELIVERY_SENT,
    NotificationDelivery,
)
from app.models.organization import Organization
from app.models.outbox import OutboxEvent
from app.models.tenant import Tenant
from app.services.notification import (
    DEFAULT_MAX_ATTEMPTS,
    NotificationService,
    _extract_notification_delivery_id,
    outbox_notification_requested_handler,
)
from app.services.notification_providers import (
    FailingNotificationProvider,
    LogNotificationProvider,
)
from app.services.outbox import OutboxService


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
    org = Organization(name="Notif Org", domain=f"notif-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="Notif Tenant",
        organization_id=org.id,
        location_code=f"N-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


@pytest.mark.asyncio
async def test_create_template_and_schedule_renders_body(db_session, tenant):
    svc = NotificationService(db_session)
    tmpl = await svc.create_template(
        tenant.id,
        code="welcome",
        name="Welcome email",
        channel="EMAIL",
        subject_template="Hi $first_name",
        body_template="Hello $first_name, welcome to $gym_name!",
    )
    await db_session.commit()
    assert tmpl.code == "welcome"
    assert tmpl.channel == "EMAIL"

    result = await svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_address="member@example.com",
        template_code="welcome",
        context={"first_name": "Ada", "gym_name": "GymClub"},
        enqueue_outbox=False,
    )
    await db_session.commit()

    assert result.created is True
    d = result.delivery
    assert d.subject == "Hi Ada"
    assert d.body == "Hello Ada, welcome to GymClub!"
    assert d.template_id == tmpl.id
    assert d.status == "PENDING"


@pytest.mark.asyncio
async def test_schedule_delivery_dedupe_key_idempotent(db_session, tenant):
    svc = NotificationService(db_session)
    await svc.create_template(
        tenant.id,
        code="otp",
        name="OTP",
        channel="SMS",
        body_template="Code $code",
    )
    await db_session.commit()

    a = await svc.schedule_delivery(
        tenant.id,
        channel="SMS",
        recipient_address="+15551212",
        template_code="otp",
        context={"code": "1234"},
        dedupe_key="otp:user-1",
        enqueue_outbox=False,
    )
    await db_session.commit()
    b = await svc.schedule_delivery(
        tenant.id,
        channel="SMS",
        recipient_address="+15551212",
        template_code="otp",
        context={"code": "9999"},
        dedupe_key="otp:user-1",
        enqueue_outbox=False,
    )
    await db_session.commit()

    assert a.created is True
    assert b.created is False
    assert a.delivery.id == b.delivery.id
    # Original body retained (idempotent; not re-rendered)
    assert a.delivery.body == "Code 1234"


@pytest.mark.asyncio
async def test_dispatch_delivery_log_provider_sent(db_session, tenant):
    log = LogNotificationProvider()
    svc = NotificationService(
        db_session,
        providers={"EMAIL": log, "SMS": log, "WHATSAPP": log, "PUSH": log},
    )
    await svc.create_template(
        tenant.id,
        code="ping",
        name="Ping",
        channel="EMAIL",
        body_template="ping",
    )
    await db_session.commit()

    scheduled = await svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_address="a@b.c",
        template_code="ping",
        enqueue_outbox=False,
    )
    await db_session.commit()

    out = await svc.dispatch_delivery(tenant.id, scheduled.delivery.id)
    await db_session.commit()

    assert out.status == DELIVERY_SENT
    assert out.provider == "log"
    assert out.provider_message_id is not None
    assert out.provider_message_id.startswith("log-")
    assert out.sent_at is not None
    assert out.attempt_count == 1


@pytest.mark.asyncio
async def test_schedule_enqueue_outbox_notification_requested(db_session, tenant):
    svc = NotificationService(db_session)
    await svc.create_template(
        tenant.id,
        code="billing",
        name="Billing",
        channel="EMAIL",
        body_template="Invoice ready",
    )
    await db_session.commit()

    result = await svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_address="bill@example.com",
        template_code="billing",
        enqueue_outbox=True,
    )
    await db_session.commit()

    assert result.created is True
    assert result.delivery.status == DELIVERY_QUEUED
    assert result.outbox_event_id is not None

    row = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.id == result.outbox_event_id)
        )
    ).scalar_one()
    assert row.event_type == NOTIFICATION_REQUESTED_V1
    assert row.status == "PENDING"
    assert row.aggregate_type == "notification_delivery"
    assert row.aggregate_id == result.delivery.id
    # Envelope: delivery_id under data
    payload = row.payload
    assert isinstance(payload, dict)
    data = payload.get("data", payload)
    assert data.get("delivery_id") == str(result.delivery.id)


@pytest.mark.asyncio
async def test_outbox_publisher_handler_dispatches_delivery(db_session, tenant):
    svc = NotificationService(db_session)
    await svc.create_template(
        tenant.id,
        code="dispatch-via-outbox",
        name="Via Outbox",
        channel="EMAIL",
        body_template="Outbox path $name",
    )
    await db_session.commit()

    scheduled = await svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_address="outbox@example.com",
        template_code="dispatch-via-outbox",
        context={"name": "Phase16"},
        enqueue_outbox=True,
    )
    await db_session.commit()
    delivery_id = scheduled.delivery.id

    outbox = OutboxService(db_session)
    claimed = await outbox.claim_pending(tenant_id=tenant.id, worker_id="w-notif-pub")
    await db_session.commit()
    assert len(claimed) == 1
    assert claimed[0].event_type == NOTIFICATION_REQUESTED_V1
    assert claimed[0].status == "PROCESSING"

    async def publisher(ev: OutboxEvent) -> None:
        await outbox_notification_requested_handler(db_session, ev)

    stats = await outbox.dispatch_claimed(claimed, publisher, worker_id="w-notif-pub")
    await db_session.commit()
    assert stats["published"] == 1

    delivery = (
        await db_session.execute(
            select(NotificationDelivery).where(NotificationDelivery.id == delivery_id)
        )
    ).scalar_one()
    assert delivery.status == DELIVERY_SENT
    assert delivery.provider == "log"
    assert delivery.provider_message_id is not None
    assert "Phase16" in (delivery.body or "")

    ob = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.id == claimed[0].id)
        )
    ).scalar_one()
    assert ob.status == "PUBLISHED"


@pytest.mark.asyncio
async def test_fail_provider_then_dead_after_max_attempts(db_session, tenant):
    fail = FailingNotificationProvider()
    svc = NotificationService(
        db_session,
        providers={"EMAIL": fail, "SMS": fail, "WHATSAPP": fail, "PUSH": fail},
    )
    await svc.create_template(
        tenant.id,
        code="fail-path",
        name="Fail Path",
        channel="EMAIL",
        body_template="x",
    )
    await db_session.commit()

    scheduled = await svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_address="fail@example.com",
        template_code="fail-path",
        enqueue_outbox=False,
    )
    await db_session.commit()

    max_attempts = 3
    last = None
    for _ in range(max_attempts):
        last = await svc.dispatch_delivery(
            tenant.id, scheduled.delivery.id, max_attempts=max_attempts
        )
        await db_session.commit()

    assert last is not None
    assert last.status == DELIVERY_DEAD
    assert last.attempt_count == max_attempts
    assert last.error_message == "provider_forced_failure"


@pytest.mark.asyncio
async def test_process_due_failed_retries_and_sends(db_session, tenant):
    fail = FailingNotificationProvider()
    log = LogNotificationProvider()
    svc = NotificationService(
        db_session,
        providers={"EMAIL": fail},
    )
    await svc.create_template(
        tenant.id,
        code="retry-path",
        name="Retry Path",
        channel="EMAIL",
        body_template="retry",
    )
    await db_session.commit()

    scheduled = await svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_address="retry@example.com",
        template_code="retry-path",
        enqueue_outbox=False,
    )
    await db_session.commit()

    from datetime import UTC, datetime, timedelta

    failed = await svc.dispatch_delivery(tenant.id, scheduled.delivery.id)
    await db_session.commit()
    assert failed.status == DELIVERY_FAILED

    # Make row due for retry (dispatch sets available_at = now + 30s)
    failed.available_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.flush()
    await db_session.commit()

    # Swap to log provider and process due failed
    svc.providers = {"EMAIL": log}
    stats = await svc.process_due_failed(tenant.id, max_attempts=5)
    await db_session.commit()
    assert stats["sent"] == 1

    row = (
        await db_session.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.id == scheduled.delivery.id
            )
        )
    ).scalar_one()
    assert row.status == DELIVERY_SENT


@pytest.mark.asyncio
async def test_recipient_user_id_must_belong_to_tenant(db_session, tenant):
    """Foreign users (no UserRole for tenant) are rejected at schedule."""
    from app.models.rbac import Role, UserRole
    from app.models.user import User

    svc = NotificationService(db_session)
    await svc.create_template(
        tenant.id,
        code="rcpt-bind",
        name="Rcpt Bind",
        channel="EMAIL",
        body_template="hi",
    )
    await db_session.commit()

    foreign = User(
        email=f"foreign-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    local = User(
        email=f"local-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db_session.add_all([foreign, local])
    await db_session.flush()
    role = Role(name=f"member-{uuid4().hex[:8]}", description="t", is_system=False)
    db_session.add(role)
    await db_session.flush()
    db_session.add(UserRole(user_id=local.id, role_id=role.id, tenant_id=tenant.id))
    await db_session.commit()

    with pytest.raises(ValueError, match="recipient_not_in_tenant"):
        await svc.schedule_delivery(
            tenant.id,
            channel="EMAIL",
            recipient_user_id=foreign.id,
            body="hello",
            enqueue_outbox=False,
        )

    ok = await svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_user_id=local.id,
        body="hello",
        enqueue_outbox=False,
    )
    await db_session.commit()
    assert ok.created is True
    assert ok.delivery.recipient_user_id == local.id


@pytest.mark.asyncio
async def test_recipient_address_empty_or_whitespace_rejected(db_session, tenant):
    svc = NotificationService(db_session)
    with pytest.raises(ValueError, match="recipient_address_empty"):
        await svc.schedule_delivery(
            tenant.id,
            channel="EMAIL",
            recipient_address="   ",
            body="x",
            enqueue_outbox=False,
        )
    with pytest.raises(ValueError, match="recipient_required"):
        await svc.schedule_delivery(
            tenant.id,
            channel="EMAIL",
            body="x",
            enqueue_outbox=False,
        )


@pytest.mark.asyncio
async def test_outbox_handler_raises_on_failed_delivery_marks_outbox_failed(
    db_session, tenant, monkeypatch
):
    """Provider fail → handler raises → dispatch_claimed mark_failed (retry path)."""
    fail = FailingNotificationProvider()

    def _failing_providers():
        return {"EMAIL": fail, "SMS": fail, "WHATSAPP": fail, "PUSH": fail}

    monkeypatch.setattr(
        "app.services.notification.default_providers", _failing_providers
    )

    svc = NotificationService(db_session, providers=_failing_providers())
    await svc.create_template(
        tenant.id,
        code="outbox-fail",
        name="Outbox Fail",
        channel="EMAIL",
        body_template="fail",
    )
    await db_session.commit()

    scheduled = await svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_address="fail-outbox@example.com",
        template_code="outbox-fail",
        enqueue_outbox=True,
    )
    await db_session.commit()
    delivery_id = scheduled.delivery.id
    outbox_id = scheduled.outbox_event_id
    assert outbox_id is not None

    outbox = OutboxService(db_session)
    claimed = await outbox.claim_pending(tenant_id=tenant.id, worker_id="w-notif-fail")
    await db_session.commit()
    assert len(claimed) == 1

    async def publisher(ev: OutboxEvent) -> None:
        await outbox_notification_requested_handler(db_session, ev)

    stats = await outbox.dispatch_claimed(claimed, publisher, worker_id="w-notif-fail")
    await db_session.commit()
    assert stats["failed"] == 1
    assert stats["published"] == 0

    delivery = (
        await db_session.execute(
            select(NotificationDelivery).where(NotificationDelivery.id == delivery_id)
        )
    ).scalar_one()
    assert delivery.status == DELIVERY_FAILED

    ob = (
        await db_session.execute(select(OutboxEvent).where(OutboxEvent.id == outbox_id))
    ).scalar_one()
    assert ob.status == "FAILED"
    assert ob.error_message is not None
    assert "notification_delivery_not_sent" in ob.error_message


@pytest.mark.asyncio
async def test_fail_then_process_due_failed_until_dead(db_session, tenant):
    """Failing provider → FAILED → process_due_failed retries → DEAD at max_attempts."""
    from datetime import UTC, datetime, timedelta

    fail = FailingNotificationProvider()
    svc = NotificationService(
        db_session,
        providers={"EMAIL": fail, "SMS": fail, "WHATSAPP": fail, "PUSH": fail},
    )
    await svc.create_template(
        tenant.id,
        code="fail-due-dead",
        name="Fail Due Dead",
        channel="EMAIL",
        body_template="x",
    )
    await db_session.commit()

    scheduled = await svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_address="due-dead@example.com",
        template_code="fail-due-dead",
        enqueue_outbox=False,
    )
    await db_session.commit()

    max_attempts = 3
    first = await svc.dispatch_delivery(
        tenant.id, scheduled.delivery.id, max_attempts=max_attempts
    )
    await db_session.commit()
    assert first.status == DELIVERY_FAILED
    assert first.attempt_count == 1

    dead_seen = False
    # Remaining attempts go through process_due_failed (not direct dispatch loop)
    for _ in range(max_attempts):
        row = (
            await db_session.execute(
                select(NotificationDelivery).where(
                    NotificationDelivery.id == scheduled.delivery.id
                )
            )
        ).scalar_one()
        if row.status == DELIVERY_DEAD:
            dead_seen = True
            break
        if row.status == DELIVERY_FAILED:
            row.available_at = datetime.now(UTC) - timedelta(seconds=1)
            await db_session.flush()
            await db_session.commit()
        stats = await svc.process_due_failed(tenant.id, max_attempts=max_attempts)
        await db_session.commit()
        if stats.get("dead", 0) >= 1:
            dead_seen = True
            break

    final = (
        await db_session.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.id == scheduled.delivery.id
            )
        )
    ).scalar_one()
    assert dead_seen or final.status == DELIVERY_DEAD
    assert final.status == DELIVERY_DEAD
    assert final.attempt_count == max_attempts
    assert final.error_message == "provider_forced_failure"


@pytest.mark.asyncio
async def test_outbox_handler_dead_delivery_marks_outbox_published(
    db_session, tenant, monkeypatch
):
    """IR-007: this dispatch promotes to DEAD → handler OK → outbox PUBLISHED (no burn)."""
    fail = FailingNotificationProvider()

    def _failing_providers():
        return {"EMAIL": fail, "SMS": fail, "WHATSAPP": fail, "PUSH": fail}

    monkeypatch.setattr(
        "app.services.notification.default_providers", _failing_providers
    )

    svc = NotificationService(db_session, providers=_failing_providers())
    await svc.create_template(
        tenant.id,
        code="outbox-dead",
        name="Outbox Dead",
        channel="EMAIL",
        body_template="dead",
    )
    await db_session.commit()

    scheduled = await svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_address="dead-outbox@example.com",
        template_code="outbox-dead",
        enqueue_outbox=True,
    )
    await db_session.commit()
    delivery_id = scheduled.delivery.id
    outbox_id = scheduled.outbox_event_id
    assert outbox_id is not None

    # Next dispatch attempt_count becomes DEFAULT_MAX_ATTEMPTS → DEAD.
    # (Cannot monkeypatch DEFAULT_MAX_ATTEMPTS: default arg bound at def time.)
    row = (
        await db_session.execute(
            select(NotificationDelivery).where(NotificationDelivery.id == delivery_id)
        )
    ).scalar_one()
    row.attempt_count = DEFAULT_MAX_ATTEMPTS - 1
    await db_session.flush()
    await db_session.commit()

    outbox = OutboxService(db_session)
    claimed = await outbox.claim_pending(tenant_id=tenant.id, worker_id="w-notif-dead")
    await db_session.commit()
    assert len(claimed) == 1

    async def publisher(ev: OutboxEvent) -> None:
        await outbox_notification_requested_handler(db_session, ev)

    stats = await outbox.dispatch_claimed(claimed, publisher, worker_id="w-notif-dead")
    await db_session.commit()
    assert stats["published"] == 1
    assert stats["failed"] == 0

    delivery = (
        await db_session.execute(
            select(NotificationDelivery).where(NotificationDelivery.id == delivery_id)
        )
    ).scalar_one()
    assert delivery.status == DELIVERY_DEAD
    assert delivery.attempt_count == DEFAULT_MAX_ATTEMPTS

    ob = (
        await db_session.execute(select(OutboxEvent).where(OutboxEvent.id == outbox_id))
    ).scalar_one()
    assert ob.status == "PUBLISHED"


@pytest.mark.asyncio
async def test_outbox_handler_does_not_raise_on_dead_or_cancelled(db_session, tenant):
    """IR-007: pre-terminal DEAD/CANCELLED → handler succeeds (no outbox burn)."""
    svc = NotificationService(db_session)
    await svc.create_template(
        tenant.id,
        code="dead-ok",
        name="Dead Ok",
        channel="EMAIL",
        body_template="x",
    )
    await db_session.commit()

    scheduled = await svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_address="dead-ok@example.com",
        template_code="dead-ok",
        enqueue_outbox=True,
    )
    await db_session.commit()
    delivery = scheduled.delivery
    outbox_id = scheduled.outbox_event_id
    assert outbox_id is not None

    # Terminal DEAD before dispatch — handler must not raise
    delivery.status = DELIVERY_DEAD
    delivery.error_message = "already_dead"
    await db_session.flush()
    await db_session.commit()

    outbox = OutboxService(db_session)
    claimed = await outbox.claim_pending(tenant_id=tenant.id, worker_id="w-dead-ok")
    await db_session.commit()
    assert len(claimed) == 1

    async def publisher(ev: OutboxEvent) -> None:
        await outbox_notification_requested_handler(db_session, ev)

    stats = await outbox.dispatch_claimed(claimed, publisher, worker_id="w-dead-ok")
    await db_session.commit()
    assert stats["published"] == 1
    assert stats["failed"] == 0

    ob = (
        await db_session.execute(select(OutboxEvent).where(OutboxEvent.id == outbox_id))
    ).scalar_one()
    assert ob.status == "PUBLISHED"

    # CANCELLED path: fresh delivery + outbox
    scheduled2 = await svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_address="cancel-ok@example.com",
        template_code="dead-ok",
        enqueue_outbox=True,
    )
    await db_session.commit()
    delivery2 = scheduled2.delivery
    outbox_id2 = scheduled2.outbox_event_id
    delivery2.status = DELIVERY_CANCELLED
    await db_session.flush()
    await db_session.commit()

    claimed2 = await outbox.claim_pending(tenant_id=tenant.id, worker_id="w-cancel-ok")
    await db_session.commit()
    assert len(claimed2) == 1
    stats2 = await outbox.dispatch_claimed(claimed2, publisher, worker_id="w-cancel-ok")
    await db_session.commit()
    assert stats2["published"] == 1
    assert stats2["failed"] == 0
    ob2 = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.id == outbox_id2)
        )
    ).scalar_one()
    assert ob2.status == "PUBLISHED"


@pytest.mark.asyncio
async def test_handle_notification_requested_shares_parse_and_raise_policy(
    db_session, tenant, monkeypatch
):
    """IR-006: instance method delegates to module handler (shared parse/raise)."""
    fail = FailingNotificationProvider()

    def _failing_providers():
        return {"EMAIL": fail, "SMS": fail, "WHATSAPP": fail, "PUSH": fail}

    # Module handler builds a fresh NotificationService(db) → default_providers.
    monkeypatch.setattr(
        "app.services.notification.default_providers", _failing_providers
    )

    svc = NotificationService(db_session, providers=_failing_providers())
    await svc.create_template(
        tenant.id,
        code="shared-handler",
        name="Shared Handler",
        channel="EMAIL",
        body_template="shared",
    )
    await db_session.commit()

    scheduled = await svc.schedule_delivery(
        tenant.id,
        channel="EMAIL",
        recipient_address="shared@example.com",
        template_code="shared-handler",
        enqueue_outbox=True,
    )
    await db_session.commit()

    outbox_row = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.id == scheduled.outbox_event_id)
        )
    ).scalar_one()

    # Shared parse helper accepts OutboxEvent payload shape
    extracted = _extract_notification_delivery_id(outbox_row)
    assert extracted == scheduled.delivery.id

    # Instance path uses same raise policy as module handler (FAILED → raise)
    with pytest.raises(RuntimeError, match="notification_delivery_not_sent:FAILED"):
        await svc.handle_notification_requested(db_session, outbox_row)

    delivery = (
        await db_session.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.id == scheduled.delivery.id
            )
        )
    ).scalar_one()
    assert delivery.status == DELIVERY_FAILED
