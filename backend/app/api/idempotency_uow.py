"""Thin unit-of-work helper for idempotent API handlers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.idempotency import (
    IdempotencyOutcome,
    IdempotencyService,
)


async def run_idempotent[T](
    db: AsyncSession,
    *,
    tenant_id: UUID,
    operation: str,
    key: str,
    request_payload: Any,
    business: Callable[[], Awaitable[tuple[T, int, dict[str, Any] | None]]],
    resource_type: str | None = None,
    resource_id_from_result: Callable[[T], UUID | None] | None = None,
) -> T:
    """
    business() must return (result, http_status_for_cache, response_body_dict).
    On REPLAY, raises HTTPException with stored status/body OR returns via special path.

    For REPLAY of successful responses, raises HTTPException is not ideal for 200 —
    we return a special approach: business returns value; for REPLAY we reconstruct
    by raising ReplayResult.
    """
    request_hash = IdempotencyService.canonical_request_hash(request_payload)
    owner = uuid4().hex
    begin = await IdempotencyService.begin(
        db,
        tenant_id,
        operation,
        key,
        request_hash,
        owner_token=owner,
    )

    if begin.outcome == IdempotencyOutcome.CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "IDEMPOTENCY_CONFLICT",
                "message": "Idempotency-Key reused with a different request payload",
            },
        )
    if begin.outcome == IdempotencyOutcome.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "IDEMPOTENCY_IN_PROGRESS",
                "message": "Request with this Idempotency-Key is still processing",
                "retry_after_seconds": begin.retry_after_seconds or 1,
            },
            headers={"Retry-After": str(begin.retry_after_seconds or 1)},
        )
    if begin.outcome == IdempotencyOutcome.REPLAY:
        # Prefer returning body via HTTPException for non-2xx, else use ReplayEnvelope
        body = begin.response_body or {}
        code = begin.response_status or 200
        if code >= 400:
            raise HTTPException(status_code=code, detail=body)
        return ReplayResult(status_code=code, body=body)  # type: ignore[return-value]

    assert begin.record is not None
    try:
        result, http_status, response_body = await business()
        rid = None
        if resource_id_from_result is not None:
            rid = resource_id_from_result(result)
        await IdempotencyService.complete(
            db,
            begin.record,
            owner_token=owner,
            response_status=http_status,
            response_body=response_body,
            resource_type=resource_type,
            resource_id=rid,
        )
        await db.commit()
        return result
    except HTTPException as he:
        # Cache client/business HTTP errors as FAILED? Prefer not to lock out retries for 400.
        # Mark failed only for unexpected; re-raise 4xx without FAILED to allow retry.
        if he.status_code >= 500 and begin.record is not None:
            await IdempotencyService.fail(
                db,
                begin.record,
                owner_token=owner,
                response_status=he.status_code,
                response_body={"detail": he.detail}
                if not isinstance(he.detail, dict)
                else he.detail,
            )
            await db.commit()
        else:
            # release lease by failing softly so retries work for validation errors
            if begin.record is not None:
                await IdempotencyService.fail(
                    db,
                    begin.record,
                    owner_token=owner,
                    response_status=he.status_code,
                    response_body={"detail": he.detail}
                    if not isinstance(he.detail, dict)
                    else he.detail,
                )
                await db.commit()
        raise
    except Exception as e:
        if begin.record is not None:
            await IdempotencyService.fail(
                db,
                begin.record,
                owner_token=owner,
                response_status=500,
                response_body={"error": str(e)},
            )
            await db.commit()
        raise


class ReplayResult:
    """Marker returned when an idempotent success is replayed."""

    def __init__(self, status_code: int, body: dict[str, Any]):
        self.status_code = status_code
        self.body = body


def materialize_replay(result: Any, response: Response) -> Any:
    """If result is ReplayResult, set status and return body; else pass through."""
    if isinstance(result, ReplayResult):
        response.status_code = result.status_code
        return result.body
    return result
