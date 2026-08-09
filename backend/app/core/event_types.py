"""Versioned domain event type contracts (Phase 15.5C).

Outbox enqueue requires ``<domain>.<action>.v<number>`` so Phase 16 consumers
do not bind to unversioned strings.

Inbox provider raw types may differ until webhook adapters normalize them;
pattern enforcement is applied on outbox production path.
"""

from __future__ import annotations

import re

# domain.action.vN — e.g. membership.renewed.v1, payment.received.v1
EVENT_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*\.v[1-9][0-9]*$")

# Named constants for known / planned contracts (not an exhaustive runtime allowlist).
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


class EventTypeValidationError(ValueError):
    """event_type failed versioned contract validation."""


def validate_event_type(event_type: str) -> str:
    """Return event_type if valid; raise EventTypeValidationError otherwise."""
    if not event_type or not isinstance(event_type, str):
        raise EventTypeValidationError("event_type_required")
    if not EVENT_TYPE_PATTERN.fullmatch(event_type):
        raise EventTypeValidationError(
            f"event_type_must_match_domain.action.vN (got {event_type!r})"
        )
    return event_type
