"""Phase 15.5C/15.5D P1-C — versioned event_type pattern + registry allowlist."""

import pytest

from app.core.event_types import (
    CHECKIN_CREATED_V1,
    MEMBER_CREATED_V1,
    MEMBERSHIP_ACTIVATED_V1,
    MEMBERSHIP_CANCELLED_V1,
    MEMBERSHIP_RENEWED_V1,
    NOTIFICATION_EMAIL_V1,
    NOTIFICATION_REQUESTED_V1,
    PAYMENT_CAPTURED_V1,
    PAYMENT_RECEIVED_V1,
    PAYMENT_REFUNDED_V1,
    REGISTERED_EVENT_TYPES,
    TEST_EVENT_V1,
    TEST_JOB_V1,
    EventTypeValidationError,
    is_registered_event_type,
    validate_event_type,
)

# Every named constant must appear in the registry (and vice versa for public API).
_ALL_CONSTANTS = (
    MEMBERSHIP_ACTIVATED_V1,
    MEMBERSHIP_RENEWED_V1,
    MEMBERSHIP_CANCELLED_V1,
    PAYMENT_RECEIVED_V1,
    PAYMENT_CAPTURED_V1,
    PAYMENT_REFUNDED_V1,
    MEMBER_CREATED_V1,
    CHECKIN_CREATED_V1,
    NOTIFICATION_REQUESTED_V1,
    NOTIFICATION_EMAIL_V1,
    TEST_JOB_V1,
    TEST_EVENT_V1,
)


@pytest.mark.parametrize(
    "ok",
    [
        "membership.renewed.v1",
        "payment.received.v1",
        "notification.requested.v1",
        "test.job.v1",
        "test.event.v1",
        MEMBERSHIP_RENEWED_V1,
        *_ALL_CONSTANTS,
    ],
)
def test_registered_event_types_allowed(ok: str):
    assert validate_event_type(ok) == ok
    assert is_registered_event_type(ok)


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "membership.renewed",
        "membership.renewed.v0",
        "Membership.renewed.v1",
        "a.v1",
        "job.v1",
        "notify.email",
        "stripe.payment_intent.succeeded",
        "x",
    ],
)
def test_malformed_event_types_denied(bad: str):
    with pytest.raises(EventTypeValidationError):
        validate_event_type(bad)


@pytest.mark.parametrize(
    "unknown",
    [
        "whatever.typo.v99",
        "other.event.v1",
        "test.a.v1",
        "foo.bar.v1",
        "membership.activated.v2",
    ],
)
def test_wellformed_unregistered_denied(unknown: str):
    with pytest.raises(EventTypeValidationError, match="event_type_not_registered"):
        validate_event_type(unknown)
    assert not is_registered_event_type(unknown)


def test_constants_match_registry():
    from_constants = frozenset(_ALL_CONSTANTS)
    assert from_constants == REGISTERED_EVENT_TYPES
    assert len(REGISTERED_EVENT_TYPES) == len(_ALL_CONSTANTS)


def test_empty_and_non_string_required():
    with pytest.raises(EventTypeValidationError, match="event_type_required"):
        validate_event_type("")
    with pytest.raises(EventTypeValidationError, match="event_type_required"):
        validate_event_type(None)  # type: ignore[arg-type]
