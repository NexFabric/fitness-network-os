"""API-layer helpers for Phase 12 idempotency outcomes.

Endpoints can map these exceptions to HTTP 409 / 409+Retry-After without
coupling HTTP details into the domain service.
"""

from __future__ import annotations


class IdempotencyConflictError(Exception):
    """Same Idempotency-Key used with a different request body/hash."""

    def __init__(self, message: str = "Idempotency key conflict") -> None:
        super().__init__(message)


class IdempotencyInProgressError(Exception):
    """Another request still holds the processing lease for this key."""

    def __init__(
        self,
        message: str = "Idempotent request still in progress",
        *,
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds
