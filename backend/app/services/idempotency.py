"""Phase 12 real idempotency engine — begin / complete / fail (flush only).

Domain services and API handlers use this as a Unit-of-Work participant:
callers commit; this module only flushes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idempotency import IdempotencyRecord, IdempotencyStatus

# ---------------------------------------------------------------------------
# Documented operation names (stable wire / store keys)
# ---------------------------------------------------------------------------

FINANCE_INVOICE_CREATE = "finance.invoice.create"
FINANCE_PAYMENT_CREATE = "finance.payment.create"
FINANCE_REFUND_CREATE = "finance.refund.create"
FINANCE_CREDIT_ISSUE = "finance.credit.issue"
ENTITLEMENT_CONSUME = "entitlements.consume"


class IdempotencyOutcome(str, Enum):
    PROCEED = "PROCEED"  # caller should run business logic
    REPLAY = "REPLAY"  # return cached response
    CONFLICT = "CONFLICT"  # same key, different request hash
    IN_PROGRESS = "IN_PROGRESS"  # lease held by another worker


@dataclass
class IdempotencyBeginResult:
    outcome: IdempotencyOutcome
    record: IdempotencyRecord | None = None
    response_status: int | None = None
    response_body: dict | None = None
    retry_after_seconds: int | None = None


def _status_value(status: IdempotencyStatus | str) -> str:
    return status.value if isinstance(status, IdempotencyStatus) else str(status)


def _retry_after_seconds(locked_until: datetime, now: datetime) -> int:
    delta = (locked_until - now).total_seconds()
    return max(1, int(delta) if delta == int(delta) else int(delta) + 1)


class IdempotencyService:
    """Lease-based idempotency store for critical mutating operations."""

    @staticmethod
    def canonical_request_hash(payload: Any) -> str:
        """SHA-256 of canonical JSON (sorted keys, compact separators)."""
        canonical = json.dumps(
            payload,
            sort_keys=True,
            default=str,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    async def begin(
        session: AsyncSession,
        tenant_id: UUID,
        operation: str,
        key: str,
        request_hash: str,
        *,
        ttl_seconds: int = 86400,
        lease_seconds: int = 30,
        owner_token: str,
    ) -> IdempotencyBeginResult:
        """
        Acquire or resolve an idempotency record for (tenant, operation, key).

        Flush only — no commit. Concurrent inserts resolve via SELECT FOR UPDATE.
        """
        now = datetime.now(UTC)
        record = IdempotencyRecord(
            tenant_id=tenant_id,
            operation=operation,
            key=key,
            request_hash=request_hash,
            status=IdempotencyStatus.PROCESSING.value,
            expires_at=now + timedelta(seconds=ttl_seconds),
            locked_until=now + timedelta(seconds=lease_seconds),
            owner_token=owner_token,
            attempt_count=1,
        )

        try:
            # Savepoint so IntegrityError does not abort the outer UoW transaction.
            async with session.begin_nested():
                session.add(record)
                await session.flush()
            return IdempotencyBeginResult(
                outcome=IdempotencyOutcome.PROCEED,
                record=record,
            )
        except IntegrityError:
            pass

        existing = (
            await session.execute(
                select(IdempotencyRecord)
                .where(
                    IdempotencyRecord.tenant_id == tenant_id,
                    IdempotencyRecord.operation == operation,
                    IdempotencyRecord.key == key,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()

        if existing is None:
            raise RuntimeError(
                "Idempotency unique conflict but row not found for "
                f"tenant={tenant_id} operation={operation} key={key}"
            )

        return await IdempotencyService._resolve_existing(
            session,
            existing,
            request_hash=request_hash,
            lease_seconds=lease_seconds,
            owner_token=owner_token,
            now=now,
        )

    @staticmethod
    async def _resolve_existing(
        session: AsyncSession,
        record: IdempotencyRecord,
        *,
        request_hash: str,
        lease_seconds: int,
        owner_token: str,
        now: datetime,
    ) -> IdempotencyBeginResult:
        status = _status_value(record.status)

        if status == IdempotencyStatus.SUCCEEDED.value:
            if record.request_hash != request_hash:
                return IdempotencyBeginResult(
                    outcome=IdempotencyOutcome.CONFLICT,
                    record=record,
                )
            return IdempotencyBeginResult(
                outcome=IdempotencyOutcome.REPLAY,
                record=record,
                response_status=record.response_status,
                response_body=record.response_body,
            )

        if status == IdempotencyStatus.PROCESSING.value:
            locked_until = record.locked_until
            if locked_until is not None and locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=UTC)
            if locked_until is not None and locked_until > now:
                return IdempotencyBeginResult(
                    outcome=IdempotencyOutcome.IN_PROGRESS,
                    record=record,
                    retry_after_seconds=_retry_after_seconds(locked_until, now),
                )

            # Lease expired — reclaim only if request hash matches.
            if record.request_hash != request_hash:
                return IdempotencyBeginResult(
                    outcome=IdempotencyOutcome.CONFLICT,
                    record=record,
                )

            record.owner_token = owner_token
            record.locked_until = now + timedelta(seconds=lease_seconds)
            record.attempt_count = (record.attempt_count or 0) + 1
            await session.flush()
            return IdempotencyBeginResult(
                outcome=IdempotencyOutcome.PROCEED,
                record=record,
            )

        if status == IdempotencyStatus.FAILED.value:
            # Allow retry with new lease / hash.
            record.status = IdempotencyStatus.PROCESSING.value
            record.request_hash = request_hash
            record.owner_token = owner_token
            record.locked_until = now + timedelta(seconds=lease_seconds)
            record.attempt_count = (record.attempt_count or 0) + 1
            record.response_status = None
            record.response_body = None
            record.completed_at = None
            record.resource_type = None
            record.resource_id = None
            await session.flush()
            return IdempotencyBeginResult(
                outcome=IdempotencyOutcome.PROCEED,
                record=record,
            )

        raise RuntimeError(f"Unknown idempotency status: {status!r}")

    @staticmethod
    async def complete(
        session: AsyncSession,
        record: IdempotencyRecord,
        *,
        response_status: int,
        response_body: dict | None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        owner_token: str,
    ) -> IdempotencyRecord:
        """Mark record SUCCEEDED and cache response. Flush only."""
        if record.owner_token != owner_token:
            raise ValueError("Idempotency lease owner mismatch")

        record.status = IdempotencyStatus.SUCCEEDED.value
        record.locked_until = None
        record.completed_at = datetime.now(UTC)
        record.response_status = response_status
        record.response_body = response_body
        record.resource_type = resource_type
        record.resource_id = resource_id
        await session.flush()
        return record

    @staticmethod
    async def fail(
        session: AsyncSession,
        record: IdempotencyRecord,
        *,
        owner_token: str,
        response_status: int = 500,
        response_body: dict | None = None,
    ) -> IdempotencyRecord:
        """Mark record FAILED and release lease. Flush only."""
        if record.owner_token != owner_token:
            raise ValueError("Idempotency lease owner mismatch")

        record.status = IdempotencyStatus.FAILED.value
        record.locked_until = None
        record.response_status = response_status
        record.response_body = response_body
        await session.flush()
        return record
