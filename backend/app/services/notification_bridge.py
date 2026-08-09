"""Domain → notification.requested bridge (Phase 16 helper).

Hard boundary (AGENTS / MASTER_SPEC R-006):
  Membership (and other domain services) must **not** import channel
  providers or call WhatsApp/SMS/Email SDKs.
  Correct path:
    Domain write → (optional) domain outbox event
      → orchestrator / consumer
      → NotificationBridge → NotificationService.schedule_delivery
      → outbox ``notification.requested.v1``
      → worker → provider adapter

Phase 16 ships the bridge + tests only. Do **not** import this module from
``app.services.membership`` (architecture tests forbid
``app.services.notification*`` imports there).

Phase 17/18 wiring (intended):
  1. Membership (or payment) writes in its TX and may enqueue
     ``membership.activated.v1`` (already registered) on the outbox.
  2. A dedicated consumer / application service (not MembershipService)
     handles that domain event and calls::

         bridge.schedule_for_member_user(
             tenant_id,
             user_id,
             template_code="membership_activated",
             channel="EMAIL",
             context={...},
             dedupe_key=f"membership.activated:{membership_id}",
             source_event_type=MEMBERSHIP_ACTIVATED_V1,
             source_event_id=str(outbox_or_domain_event_id),
         )

  3. That schedules delivery + ``notification.requested.v1`` in the same
     consumer TX (or a follow-up TX) without domain → provider coupling.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.notification import NotificationService, ScheduleResult
from app.services.notification_providers import NotificationProvider


class NotificationBridge:
    """Thin wrapper so domain orchestrators schedule notifications safely.

    Does not resolve Member → User itself (User ≠ Member). Callers must pass
    the bound ``user_id`` after their own resolution path.
    """

    def __init__(
        self,
        db: AsyncSession,
        *,
        providers: dict[str, NotificationProvider] | None = None,
    ) -> None:
        self._svc = NotificationService(db, providers=providers)

    @property
    def notification_service(self) -> NotificationService:
        return self._svc

    async def schedule_for_member_user(
        self,
        tenant_id: UUID,
        user_id: UUID,
        *,
        template_code: str,
        channel: str,
        context: dict[str, Any] | None = None,
        dedupe_key: str | None = None,
        correlation_id: str | None = None,
        source_event_type: str | None = None,
        source_event_id: str | None = None,
        enqueue_outbox: bool = True,
    ) -> ScheduleResult:
        """Schedule a templated delivery for a tenant-bound user.

        ``user_id`` must have a ``UserRole`` on ``tenant_id`` (enforced by
        ``NotificationService.schedule_delivery`` → ``recipient_not_in_tenant``).

        Use ``source_event_type`` / ``source_event_id`` to link back to a domain
        event (e.g. ``membership.activated.v1``) for audit/trace only — this
        method does **not** enqueue the domain event itself.
        """
        if not template_code or not str(template_code).strip():
            raise ValueError("template_code_required")
        return await self._svc.schedule_delivery(
            tenant_id,
            channel=channel,
            recipient_user_id=user_id,
            template_code=template_code,
            context=context,
            dedupe_key=dedupe_key,
            correlation_id=correlation_id,
            source_event_type=source_event_type,
            source_event_id=source_event_id,
            enqueue_outbox=enqueue_outbox,
        )

    async def schedule_from_domain_event(
        self,
        tenant_id: UUID,
        *,
        event_type: str,
        event_id: str | None,
        user_id: UUID,
        template_code: str,
        channel: str,
        context: dict[str, Any] | None = None,
        dedupe_key: str | None = None,
        correlation_id: str | None = None,
        enqueue_outbox: bool = True,
    ) -> ScheduleResult:
        """Convenience: same as schedule_for_member_user with source event refs.

        ``event_type`` is stored on the delivery as ``source_event_type`` only
        (e.g. ``MEMBERSHIP_ACTIVATED_V1``). It is **not** re-validated against
        the outbox registry here — domain producers already did that when
        enqueuing the domain event.
        """
        return await self.schedule_for_member_user(
            tenant_id,
            user_id,
            template_code=template_code,
            channel=channel,
            context=context,
            dedupe_key=dedupe_key,
            correlation_id=correlation_id,
            source_event_type=event_type,
            source_event_id=event_id,
            enqueue_outbox=enqueue_outbox,
        )
