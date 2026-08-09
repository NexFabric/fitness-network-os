"""Versioned domain event type contracts (Phase 15.5C / 15.5D P1-C).

Outbox enqueue requires ``<domain>.<action>.v<number>`` **and** membership in
the canonical registry so Phase 16 consumers do not bind to typos or ad-hoc
strings.

Inbox provider raw types may differ until webhook adapters normalize them;
pattern + registry enforcement is applied on the outbox production path only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

# domain.action.vN — e.g. membership.renewed.v1, payment.received.v1
EVENT_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*\.v[1-9][0-9]*$")


@dataclass(frozen=True)
class EventTypeSpec:
    """Canonical event type contract entry (extensible for future metadata)."""

    name: str


# Named constants for known contracts (source of truth for registry membership).
MEMBERSHIP_ACTIVATED_V1 = "membership.activated.v1"
MEMBERSHIP_RENEWED_V1 = "membership.renewed.v1"
MEMBERSHIP_CANCELLED_V1 = "membership.cancelled.v1"
PAYMENT_RECEIVED_V1 = "payment.received.v1"
PAYMENT_CAPTURED_V1 = "payment.captured.v1"
PAYMENT_REFUNDED_V1 = "payment.refunded.v1"
MEMBER_CREATED_V1 = "member.created.v1"
CHECKIN_CREATED_V1 = "checkin.created.v1"
NOTIFICATION_REQUESTED_V1 = "notification.requested.v1"
NOTIFICATION_EMAIL_V1 = "notification.email.v1"
TEST_JOB_V1 = "test.job.v1"
TEST_EVENT_V1 = "test.event.v1"

# Canonical allowlist — outbox enqueue rejects well-formed but unknown types.
_EVENT_TYPE_SPECS: Final[tuple[EventTypeSpec, ...]] = (
    EventTypeSpec(MEMBERSHIP_ACTIVATED_V1),
    EventTypeSpec(MEMBERSHIP_RENEWED_V1),
    EventTypeSpec(MEMBERSHIP_CANCELLED_V1),
    EventTypeSpec(PAYMENT_RECEIVED_V1),
    EventTypeSpec(PAYMENT_CAPTURED_V1),
    EventTypeSpec(PAYMENT_REFUNDED_V1),
    EventTypeSpec(MEMBER_CREATED_V1),
    EventTypeSpec(CHECKIN_CREATED_V1),
    EventTypeSpec(NOTIFICATION_REQUESTED_V1),
    EventTypeSpec(NOTIFICATION_EMAIL_V1),
    EventTypeSpec(TEST_JOB_V1),
    EventTypeSpec(TEST_EVENT_V1),
)

REGISTERED_EVENT_TYPES: Final[frozenset[str]] = frozenset(
    spec.name for spec in _EVENT_TYPE_SPECS
)


class EventTypeValidationError(ValueError):
    """event_type failed versioned contract validation."""


def is_registered_event_type(event_type: str) -> bool:
    """Return True if *event_type* is in the canonical registry."""
    return event_type in REGISTERED_EVENT_TYPES


def validate_event_type(event_type: str) -> str:
    """Return event_type if valid and registered; raise otherwise.

    Order: required → syntax (domain.action.vN) → registry allowlist.
    """
    if not event_type or not isinstance(event_type, str):
        raise EventTypeValidationError("event_type_required")
    if not EVENT_TYPE_PATTERN.fullmatch(event_type):
        raise EventTypeValidationError(
            f"event_type_must_match_domain.action.vN (got {event_type!r})"
        )
    if event_type not in REGISTERED_EVENT_TYPES:
        raise EventTypeValidationError(
            f"event_type_not_registered (got {event_type!r})"
        )
    return event_type
