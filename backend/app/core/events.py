"""CloudEvents-inspired standard event envelope (MASTER_SPEC / ADR-021).

Outbox payload convention: either a full envelope dict, or wrap domain data via
``build_event_envelope`` / ``envelope_for_outbox``.

Terminology: delivery is at-least-once; consumers must be idempotent for
effectively-once business effects.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

SPEC_VERSION = "1.0"
DEFAULT_SOURCE = "fitness-network-os/backend"


def build_event_envelope(
    *,
    event_type: str,
    tenant_id: UUID | str,
    data: dict[str, Any],
    event_id: str | None = None,
    source: str = DEFAULT_SOURCE,
    subject: str | None = None,
    actor_id: UUID | str | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
    occurred_at: datetime | None = None,
    aggregate_type: str | None = None,
    aggregate_id: UUID | str | None = None,
) -> dict[str, Any]:
    """Build a versioned event envelope for outbox / messaging.

    ``event_type`` should be versioned, e.g. ``membership.renewed.v1``.
    """
    if not event_type:
        raise ValueError("event_type_required")
    if not isinstance(data, dict):
        raise TypeError("data_must_be_object")
    now = occurred_at or datetime.now(UTC)
    env: dict[str, Any] = {
        "specversion": SPEC_VERSION,
        "id": event_id or str(uuid4()),
        "source": source,
        "type": event_type,
        "time": now.isoformat(),
        "tenantid": str(tenant_id),
        "data": data,
    }
    if subject is not None:
        env["subject"] = subject
    if actor_id is not None:
        env["actorid"] = str(actor_id)
    if correlation_id is not None:
        env["correlationid"] = correlation_id
    if causation_id is not None:
        env["causationid"] = causation_id
    if aggregate_type is not None:
        env["aggregatetype"] = aggregate_type
    if aggregate_id is not None:
        env["aggregateid"] = str(aggregate_id)
    return env


def envelope_for_outbox(
    tenant_id: UUID,
    event_type: str,
    data: dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    """Convenience wrapper used by domain services enqueueing outbox events."""
    return build_event_envelope(
        event_type=event_type,
        tenant_id=tenant_id,
        data=data,
        **kwargs,
    )


def is_envelope(payload: dict[str, Any]) -> bool:
    return (
        isinstance(payload, dict)
        and payload.get("specversion") == SPEC_VERSION
        and "type" in payload
        and "id" in payload
        and "data" in payload
    )
