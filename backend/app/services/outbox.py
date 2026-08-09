"""Phase 15/15.5 transactional outbox / inbox engine (flush-only).

At-least-once delivery + idempotent handlers → effectively-once effects.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import build_event_envelope, is_envelope
from app.models.outbox import InboxEvent, OutboxEvent

Handler = Callable[[AsyncSession, InboxEvent], Awaitable[None]]

DEFAULT_LEASE_SECONDS = 60
DEFAULT_MAX_ATTEMPTS = 10


@dataclass
class EnqueueResult:
    event: OutboxEvent
    created: bool


@dataclass
class InboxReceiveResult:
    event: InboxEvent
    is_duplicate: bool


class OutboxService:
    """Durable outbox enqueue + claim/publish + inbox receive/process."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def enqueue(
        self,
        tenant_id: UUID,
        event_type: str,
        payload: dict[str, Any],
        *,
        aggregate_type: str | None = None,
        aggregate_id: UUID | None = None,
        dedupe_key: str | None = None,
        available_at: datetime | None = None,
        wrap_envelope: bool = True,
        actor_id: UUID | None = None,
        correlation_id: str | None = None,
    ) -> EnqueueResult:
        if not event_type:
            raise ValueError("event_type_required")
        if not isinstance(payload, dict):
            raise TypeError("payload_must_be_object")

        if wrap_envelope and not is_envelope(payload):
            payload = build_event_envelope(
                event_type=event_type,
                tenant_id=tenant_id,
                data=payload,
                actor_id=actor_id,
                correlation_id=correlation_id,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
            )

        if dedupe_key:
            existing = await self.db.execute(
                select(OutboxEvent).where(
                    OutboxEvent.tenant_id == tenant_id,
                    OutboxEvent.dedupe_key == dedupe_key,
                )
            )
            found = existing.scalars().first()
            if found:
                return EnqueueResult(event=found, created=False)

        event = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            event_type=event_type,
            payload=payload,
            status="PENDING",
            attempt_count=0,
            available_at=available_at or datetime.now(UTC),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            dedupe_key=dedupe_key,
        )
        try:
            async with self.db.begin_nested():
                self.db.add(event)
                await self.db.flush()
        except IntegrityError:
            if dedupe_key:
                existing = await self.db.execute(
                    select(OutboxEvent).where(
                        OutboxEvent.tenant_id == tenant_id,
                        OutboxEvent.dedupe_key == dedupe_key,
                    )
                )
                found = existing.scalars().first()
                if found:
                    return EnqueueResult(event=found, created=False)
            raise
        return EnqueueResult(event=event, created=True)

    async def claim_pending(
        self,
        *,
        tenant_id: UUID | None = None,
        limit: int = 50,
        now: datetime | None = None,
        worker_id: str | None = None,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> list[OutboxEvent]:
        """Claim PENDING/FAILED-due or stale PROCESSING (lease expired) with SKIP LOCKED."""
        now = now or datetime.now(UTC)
        limit = max(1, min(limit, 200))
        worker_id = worker_id or uuid4().hex[:16]
        lease_until = now + timedelta(seconds=max(5, lease_seconds))

        claimable = or_(
            and_(
                OutboxEvent.status.in_(["PENDING", "FAILED"]),
                or_(
                    OutboxEvent.available_at.is_(None),
                    OutboxEvent.available_at <= now,
                ),
            ),
            and_(
                OutboxEvent.status == "PROCESSING",
                or_(
                    OutboxEvent.lease_until.is_(None),
                    OutboxEvent.lease_until <= now,
                ),
            ),
        )
        stmt = (
            select(OutboxEvent)
            .where(claimable)
            .order_by(OutboxEvent.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        if tenant_id is not None:
            stmt = stmt.where(OutboxEvent.tenant_id == tenant_id)

        result = await self.db.execute(stmt)
        events = list(result.scalars().all())
        for ev in events:
            ev.status = "PROCESSING"
            ev.attempt_count = (ev.attempt_count or 0) + 1
            ev.worker_id = worker_id
            ev.lease_until = lease_until
        if events:
            await self.db.flush()
        return events

    async def mark_published(self, event: OutboxEvent) -> OutboxEvent:
        event.status = "PUBLISHED"
        event.processed_at = datetime.now(UTC)
        event.error_message = None
        event.lease_until = None
        event.worker_id = None
        await self.db.flush()
        return event

    async def mark_failed(
        self,
        event: OutboxEvent,
        error: str,
        *,
        retry_after_seconds: int = 30,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> OutboxEvent:
        event.error_message = (error or "error")[:2000]
        event.lease_until = None
        event.worker_id = None
        if (event.attempt_count or 0) >= max_attempts:
            event.status = "DEAD"
        else:
            event.status = "FAILED"
            event.available_at = datetime.now(UTC) + timedelta(
                seconds=max(1, retry_after_seconds)
            )
        await self.db.flush()
        return event

    async def dispatch_claimed(
        self,
        events: list[OutboxEvent],
        publisher: Callable[[OutboxEvent], Awaitable[None]],
    ) -> dict[str, int]:
        published = failed = 0
        for ev in events:
            try:
                await publisher(ev)
                await self.mark_published(ev)
                published += 1
            except Exception as e:
                await self.mark_failed(ev, str(e))
                failed += 1
        return {"published": published, "failed": failed}

    # ----- inbox -----
    async def receive_inbox(
        self,
        tenant_id: UUID,
        *,
        event_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> InboxReceiveResult:
        if not event_id or not event_type:
            raise ValueError("event_id_and_type_required")
        if not isinstance(payload, dict):
            raise TypeError("payload_must_be_object")

        event = InboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            status="PENDING",
            attempt_count=0,
            available_at=datetime.now(UTC),
        )
        try:
            async with self.db.begin_nested():
                self.db.add(event)
                await self.db.flush()
            return InboxReceiveResult(event=event, is_duplicate=False)
        except IntegrityError:
            existing = await self.db.execute(
                select(InboxEvent).where(
                    InboxEvent.tenant_id == tenant_id,
                    InboxEvent.event_id == event_id,
                )
            )
            found = existing.scalars().first()
            if found is None:
                raise
            return InboxReceiveResult(event=found, is_duplicate=True)

    async def process_pending_inbox(
        self,
        tenant_id: UUID,
        handlers: dict[str, Handler],
        *,
        limit: int = 50,
        now: datetime | None = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        retry_after_seconds: int = 30,
    ) -> dict[str, int]:
        now = now or datetime.now(UTC)
        claimable = and_(
            InboxEvent.tenant_id == tenant_id,
            InboxEvent.status.in_(["PENDING", "FAILED"]),
            or_(
                InboxEvent.available_at.is_(None),
                InboxEvent.available_at <= now,
            ),
        )
        stmt = (
            select(InboxEvent)
            .where(claimable)
            .order_by(InboxEvent.created_at)
            .limit(max(1, min(limit, 200)))
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(stmt)
        events = list(result.scalars().all())
        processed = failed = skipped = dead = 0
        for ev in events:
            handler = handlers.get(ev.event_type)
            if handler is None:
                ev.status = "UNHANDLED"
                ev.error_message = f"no_handler:{ev.event_type}"
                skipped += 1
                await self.db.flush()
                continue
            ev.status = "PROCESSING"
            ev.attempt_count = (ev.attempt_count or 0) + 1
            await self.db.flush()
            try:
                await handler(self.db, ev)
                ev.status = "PROCESSED"
                ev.processed_at = datetime.now(UTC)
                ev.error_message = None
                processed += 1
            except Exception as e:
                ev.error_message = str(e)[:2000]
                if (ev.attempt_count or 0) >= max_attempts:
                    ev.status = "DEAD"
                    dead += 1
                else:
                    ev.status = "FAILED"
                    ev.available_at = now + timedelta(
                        seconds=max(1, retry_after_seconds)
                    )
                    failed += 1
            await self.db.flush()
        return {
            "processed": processed,
            "failed": failed,
            "skipped": skipped,
            "dead": dead,
        }
