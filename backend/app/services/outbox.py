"""Phase 15/15.5 transactional outbox / inbox engine (flush-only).

At-least-once delivery + idempotent handlers → effectively-once effects.

Phase 15.5C: no generic tenant HTTP ingress. Domain services call enqueue()
in the same DB transaction. Provider webhooks (Phase 16+) will call
receive_inbox() after signature verification and tenant resolution.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_types import validate_event_type
from app.core.events import build_event_envelope, is_envelope, validate_envelope
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
        # Versioned contract: domain.action.vN (Phase 15.5C)
        event_type = validate_event_type(event_type)
        if not isinstance(payload, dict):
            raise TypeError("payload_must_be_object")

        if wrap_envelope:
            if is_envelope(payload):
                validate_envelope(payload, tenant_id=tenant_id, event_type=event_type)
            else:
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
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> list[OutboxEvent]:
        """Claim PENDING/FAILED-due or stale PROCESSING (lease expired) with SKIP LOCKED.

        Rows with attempt_count >= max_attempts are never reclaimed. Stale
        PROCESSING rows already at the cap are moved to DEAD so they cannot
        sit forever after a worker crash without mark_failed.
        """
        now = now or datetime.now(UTC)
        limit = max(1, min(limit, 200))
        worker_id = worker_id or uuid4().hex[:16]
        lease_until = now + timedelta(seconds=max(5, lease_seconds))
        max_attempts = max(1, max_attempts)

        lease_expired = or_(
            OutboxEvent.lease_until.is_(None),
            OutboxEvent.lease_until <= now,
        )

        # Exhausted stale PROCESSING: mark DEAD instead of infinite reclaim.
        dead_stmt = (
            update(OutboxEvent)
            .where(
                OutboxEvent.status == "PROCESSING",
                lease_expired,
                OutboxEvent.attempt_count >= max_attempts,
            )
            .values(
                status="DEAD",
                error_message="max_attempts_exceeded_on_claim",
                lease_until=None,
                worker_id=None,
            )
            # Keep identity-map rows consistent (sessions often use expire_on_commit=False).
            .execution_options(synchronize_session="fetch")
        )
        if tenant_id is not None:
            dead_stmt = dead_stmt.where(OutboxEvent.tenant_id == tenant_id)
        await self.db.execute(dead_stmt)

        under_max = OutboxEvent.attempt_count < max_attempts
        claimable = and_(
            under_max,
            or_(
                and_(
                    OutboxEvent.status.in_(["PENDING", "FAILED"]),
                    or_(
                        OutboxEvent.available_at.is_(None),
                        OutboxEvent.available_at <= now,
                    ),
                ),
                and_(
                    OutboxEvent.status == "PROCESSING",
                    lease_expired,
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
            # Defensive: never reclaim over-cap rows if filter races.
            if (ev.attempt_count or 0) >= max_attempts:
                ev.status = "DEAD"
                ev.error_message = "max_attempts_exceeded_on_claim"
                ev.lease_until = None
                ev.worker_id = None
                continue
            ev.status = "PROCESSING"
            ev.attempt_count = (ev.attempt_count or 0) + 1
            ev.worker_id = worker_id
            ev.lease_until = lease_until
        claimed = [ev for ev in events if ev.status == "PROCESSING"]
        if events:
            await self.db.flush()
        return claimed

    async def mark_published(
        self, event: OutboxEvent, *, worker_id: str
    ) -> OutboxEvent:
        """CAS: only the claiming worker may publish (status=PROCESSING + worker_id)."""
        if not worker_id:
            raise ValueError("lease_ownership_lost")
        now = datetime.now(UTC)
        res = await self.db.execute(
            update(OutboxEvent)
            .where(
                OutboxEvent.id == event.id,
                OutboxEvent.tenant_id == event.tenant_id,
                OutboxEvent.status == "PROCESSING",
                OutboxEvent.worker_id == worker_id,
            )
            .values(
                status="PUBLISHED",
                processed_at=now,
                error_message=None,
                lease_until=None,
                worker_id=None,
            )
            .execution_options(synchronize_session=False)
        )
        if getattr(res, "rowcount", 0) != 1:
            raise ValueError("lease_ownership_lost")
        event.status = "PUBLISHED"
        event.processed_at = now
        event.error_message = None
        event.lease_until = None
        event.worker_id = None
        return event

    async def mark_failed(
        self,
        event: OutboxEvent,
        error: str,
        *,
        worker_id: str,
        retry_after_seconds: int = 30,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> OutboxEvent:
        """CAS: only the claiming worker may fail/retry (status=PROCESSING + worker_id)."""
        if not worker_id:
            raise ValueError("lease_ownership_lost")
        attempts = event.attempt_count or 0
        err = (error or "error")[:2000]
        if attempts >= max_attempts:
            new_status = "DEAD"
            available_at = event.available_at
        else:
            new_status = "FAILED"
            available_at = datetime.now(UTC) + timedelta(
                seconds=max(1, retry_after_seconds)
            )
        res = await self.db.execute(
            update(OutboxEvent)
            .where(
                OutboxEvent.id == event.id,
                OutboxEvent.tenant_id == event.tenant_id,
                OutboxEvent.status == "PROCESSING",
                OutboxEvent.worker_id == worker_id,
            )
            .values(
                status=new_status,
                error_message=err,
                lease_until=None,
                worker_id=None,
                available_at=available_at,
            )
            .execution_options(synchronize_session=False)
        )
        if getattr(res, "rowcount", 0) != 1:
            raise ValueError("lease_ownership_lost")
        event.status = new_status
        event.error_message = err
        event.lease_until = None
        event.worker_id = None
        event.available_at = available_at
        return event

    async def dispatch_claimed(
        self,
        events: list[OutboxEvent],
        publisher: Callable[[OutboxEvent], Awaitable[None]],
        *,
        worker_id: str | None = None,
    ) -> dict[str, int]:
        """Worker-only: ACK publisher then CAS mark_*; uses claim worker_id per event.

        Prefer passing the same worker_id used in claim_pending. Falls back to
        each event's worker_id from the claim row.
        """
        published = failed = 0
        for ev in events:
            claim_worker = worker_id or ev.worker_id
            if not claim_worker:
                failed += 1
                continue
            try:
                await publisher(ev)
            except Exception as e:
                try:
                    await self.mark_failed(ev, str(e), worker_id=claim_worker)
                except ValueError as ve:
                    if str(ve) != "lease_ownership_lost":
                        raise
                failed += 1
                continue
            try:
                await self.mark_published(ev, worker_id=claim_worker)
                published += 1
            except ValueError as ve:
                if str(ve) != "lease_ownership_lost":
                    raise
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
                # Nested savepoint: domain flushes roll back on handler failure
                async with self.db.begin_nested():
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
