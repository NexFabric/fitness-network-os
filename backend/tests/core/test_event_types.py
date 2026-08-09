"""Phase 15.5C — versioned event_type pattern."""

import pytest

from app.core.event_types import (
    MEMBERSHIP_RENEWED_V1,
    EventTypeValidationError,
    validate_event_type,
)


@pytest.mark.parametrize(
    "ok",
    [
        "membership.renewed.v1",
        "payment.received.v1",
        "notification.requested.v1",
        "test.job.v1",
        MEMBERSHIP_RENEWED_V1,
    ],
)
def test_valid_event_types(ok: str):
    assert validate_event_type(ok) == ok


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
def test_invalid_event_types(bad: str):
    with pytest.raises(EventTypeValidationError):
        validate_event_type(bad)
