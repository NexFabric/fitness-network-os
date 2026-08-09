"""Phase 16 notification service — templates, schedule, dispatch via adapters.

Flow:
  Domain / API → schedule_delivery (same DB tx optional Outbox enqueue)
  → Outbox notification.requested.v1
  → process_requested_event / dispatch_delivery → provider adapter
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from string import Template
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_types import NOTIFICATION_REQUESTED_V1
from app.core.events import is_envelope
from app.models.notification import (
    ALLOWED_CHANNELS,
    DELIVERY_CANCELLED,
    DELIVERY_DEAD,
    DELIVERY_FAILED,
    DELIVERY_PENDING,
    DELIVERY_QUEUED,
    DELIVERY_SENDING,
    DELIVERY_SENT,
    NotificationDelivery,
    NotificationTemplate,
)
from app.models.outbox import InboxEvent
from app.services.notification_providers import (
    NotificationProvider,
    default_providers,
)
from app.services.outbox import OutboxService

DEFAULT_MAX_ATTEMPTS = 5


@dataclass
class ScheduleResult:
    delivery: NotificationDelivery
    created: bool
    outbox_event_id: UUID | None = None


class NotificationService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        providers: dict[str, NotificationProvider] | None = None,
    ):
        self.db = db
        self.providers = providers or default_providers()

    # ----- templates -----
    async def create_template(
        self,
        tenant_id: UUID,
        *,
        code: str,
        name: str,
        channel: str,
        body_template: str,
        subject_template: str | None = None,
        locale: str | None = None,
    ) -> NotificationTemplate:
        code = code.strip().lower()
        channel = channel.strip().upper()
        if not code:
            raise ValueError("code_required")
        if channel not in ALLOWED_CHANNELS:
            raise ValueError(f"invalid_channel:{channel}")
        if not body_template.strip():
            raise ValueError("body_template_required")
        if not name.strip():
            raise ValueError("name_required")

        row = NotificationTemplate(
            id=uuid4(),
            tenant_id=tenant_id,
            code=code,
            name=name.strip(),
            channel=channel,
            subject_template=subject_template,
            body_template=body_template,
            is_active=True,
            locale=locale,
        )
        try:
            async with self.db.begin_nested():
                self.db.add(row)
                await self.db.flush()
        except IntegrityError as e:
            raise ValueError("template_code_conflict") from e
        return row

    async def get_template_by_code(
        self, tenant_id: UUID, code: str
    ) -> NotificationTemplate | None:
        result = await self.db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.tenant_id == tenant_id,
                NotificationTemplate.code == code.strip().lower(),
            )
        )
        return result.scalars().first()

    async def list_templates(
        self, tenant_id: UUID, *, limit: int = 50
    ) -> list[NotificationTemplate]:
        limit = max(1, min(limit, 200))
        result = await self.db.execute(
            select(NotificationTemplate)
            .where(NotificationTemplate.tenant_id == tenant_id)
            .order_by(NotificationTemplate.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # ----- schedule -----
    @staticmethod
    def _render(template: str, context: dict[str, Any]) -> str:
        # safe_substitute leaves missing keys as $name
        return Template(template).safe_substitute(**context)

    async def schedule_delivery(
        self,
        tenant_id: UUID,
        *,
        channel: str,
        recipient_address: str | None = None,
        recipient_user_id: UUID | None = None,
        template_code: str | None = None,
        subject: str | None = None,
        body: str | None = None,
        context: dict[str, Any] | None = None,
        dedupe_key: str | None = None,
        correlation_id: str | None = None,
        source_event_type: str | None = None,
        source_event_id: str | None = None,
        enqueue_outbox: bool = True,
    ) -> ScheduleResult:
        channel = channel.strip().upper()
        if channel not in ALLOWED_CHANNELS:
            raise ValueError(f"invalid_channel:{channel}")
        if not recipient_address and not recipient_user_id:
            raise ValueError("recipient_required")

        ctx = dict(context or {})
        template_id: UUID | None = None
        if template_code:
            tmpl = await self.get_template_by_code(tenant_id, template_code)
            if tmpl is None or not tmpl.is_active:
                raise ValueError("template_not_found")
            if tmpl.channel != channel:
                raise ValueError("template_channel_mismatch")
            template_id = tmpl.id
            subject = subject or (
                self._render(tmpl.subject_template, ctx)
                if tmpl.subject_template
                else None
            )
            body = body or self._render(tmpl.body_template, ctx)
        if not body:
            raise ValueError("body_required")

        if dedupe_key:
            existing = await self.db.execute(
                select(NotificationDelivery).where(
                    NotificationDelivery.tenant_id == tenant_id,
                    NotificationDelivery.dedupe_key == dedupe_key,
                )
            )
            found = existing.scalars().first()
            if found:
                return ScheduleResult(delivery=found, created=False)

        delivery = NotificationDelivery(
            id=uuid4(),
            tenant_id=tenant_id,
            template_id=template_id,
            recipient_user_id=recipient_user_id,
            recipient_address=recipient_address,
            channel=channel,
            status=DELIVERY_QUEUED if enqueue_outbox else DELIVERY_PENDING,
            subject=subject,
            body=body,
            context=ctx,
            attempt_count=0,
            available_at=datetime.now(UTC),
            dedupe_key=dedupe_key,
            source_event_type=source_event_type,
            source_event_id=source_event_id,
            correlation_id=correlation_id,
        )
        try:
            async with self.db.begin_nested():
                self.db.add(delivery)
                await self.db.flush()
        except IntegrityError:
            if dedupe_key:
                existing = await self.db.execute(
                    select(NotificationDelivery).where(
                        NotificationDelivery.tenant_id == tenant_id,
                        NotificationDelivery.dedupe_key == dedupe_key,
                    )
                )
                found = existing.scalars().first()
                if found:
                    return ScheduleResult(delivery=found, created=False)
            raise

        outbox_id: UUID | None = None
        if enqueue_outbox:
            outbox = OutboxService(self.db)
            enq = await outbox.enqueue(
                tenant_id,
                NOTIFICATION_REQUESTED_V1,
                {
                    "delivery_id": str(delivery.id),
                    "channel": channel,
                },
                aggregate_type="notification_delivery",
                aggregate_id=delivery.id,
                dedupe_key=f"notif-req:{delivery.id}",
                correlation_id=correlation_id,
            )
            outbox_id = enq.event.id

        return ScheduleResult(
            delivery=delivery, created=True, outbox_event_id=outbox_id
        )

    async def dispatch_delivery(
        self,
        tenant_id: UUID,
        delivery_id: UUID,
        *,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> NotificationDelivery:
        result = await self.db.execute(
            select(NotificationDelivery)
            .where(
                NotificationDelivery.tenant_id == tenant_id,
                NotificationDelivery.id == delivery_id,
            )
            .with_for_update()
        )
        delivery = result.scalars().first()
        if delivery is None:
            raise ValueError("delivery_not_found")
        if delivery.status in (DELIVERY_SENT, DELIVERY_CANCELLED, DELIVERY_DEAD):
            return delivery

        delivery.status = DELIVERY_SENDING
        delivery.attempt_count = (delivery.attempt_count or 0) + 1
        await self.db.flush()

        provider = self.providers.get(delivery.channel)
        if provider is None:
            delivery.error_message = f"no_provider:{delivery.channel}"
            if (delivery.attempt_count or 0) >= max_attempts:
                delivery.status = DELIVERY_DEAD
                delivery.available_at = None
            else:
                delivery.status = DELIVERY_FAILED
                delivery.available_at = datetime.now(UTC) + timedelta(seconds=30)
            await self.db.flush()
            return delivery

        res = await provider.send(delivery)
        if res.success:
            delivery.status = DELIVERY_SENT
            delivery.provider = res.provider
            delivery.provider_message_id = res.provider_message_id
            delivery.sent_at = datetime.now(UTC)
            delivery.error_message = None
            delivery.available_at = None
        else:
            delivery.provider = res.provider
            delivery.error_message = (res.error or "send_failed")[:2000]
            if (delivery.attempt_count or 0) >= max_attempts:
                delivery.status = DELIVERY_DEAD
                delivery.available_at = None
            else:
                delivery.status = DELIVERY_FAILED
                delivery.available_at = datetime.now(UTC) + timedelta(seconds=30)
        await self.db.flush()
        return delivery

    async def handle_notification_requested(
        self, _db: AsyncSession, event: InboxEvent | Any
    ) -> None:
        """Outbox/inbox-style handler: payload must include delivery_id."""
        payload = event.payload if hasattr(event, "payload") else event
        if isinstance(payload, dict) and is_envelope(payload):
            data = payload["data"]
        elif isinstance(payload, dict):
            data = payload.get("data", payload)
        else:
            raise ValueError("invalid_payload")
        if not isinstance(data, dict):
            raise TypeError("invalid_payload")
        delivery_id = data.get("delivery_id")
        if not delivery_id:
            raise ValueError("delivery_id_required")
        tenant_id = event.tenant_id
        await self.dispatch_delivery(tenant_id, UUID(str(delivery_id)))

    async def process_due_failed(
        self,
        tenant_id: UUID,
        *,
        limit: int = 50,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> dict[str, int]:
        """Retry FAILED deliveries whose available_at is due (no outbox re-inject)."""
        now = datetime.now(UTC)
        stmt = (
            select(NotificationDelivery)
            .where(
                NotificationDelivery.tenant_id == tenant_id,
                NotificationDelivery.status == DELIVERY_FAILED,
                or_(
                    NotificationDelivery.available_at.is_(None),
                    NotificationDelivery.available_at <= now,
                ),
                NotificationDelivery.attempt_count < max_attempts,
            )
            .order_by(NotificationDelivery.created_at)
            .limit(max(1, min(limit, 100)))
            .with_for_update(skip_locked=True)
        )
        rows = list((await self.db.execute(stmt)).scalars().all())
        sent = failed = dead = 0
        for d in rows:
            out = await self.dispatch_delivery(
                tenant_id, d.id, max_attempts=max_attempts
            )
            if out.status == DELIVERY_SENT:
                sent += 1
            elif out.status == DELIVERY_DEAD:
                dead += 1
            else:
                failed += 1
        return {"sent": sent, "failed": failed, "dead": dead}


async def outbox_notification_requested_handler(db: AsyncSession, event: Any) -> None:
    """Adapter for OutboxService.dispatch publisher-style or inbox handlers.

    When used as outbox *publisher*, ``event`` is OutboxEvent; when inbox, InboxEvent.
    """
    svc = NotificationService(db)
    payload = event.payload
    if isinstance(payload, dict) and is_envelope(payload):
        data = payload["data"]
    elif isinstance(payload, dict):
        data = payload.get("data", payload)
    else:
        data = {}
    if not isinstance(data, dict):
        data = {}
    delivery_id = data.get("delivery_id")
    if not delivery_id:
        raise ValueError("delivery_id_required")
    await svc.dispatch_delivery(event.tenant_id, UUID(str(delivery_id)))
