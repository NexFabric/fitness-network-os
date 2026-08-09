"""Event envelope unit tests."""

from uuid import uuid4

import pytest

from app.core.events import (
    EnvelopeValidationError,
    build_event_envelope,
    is_envelope,
    validate_envelope,
)


def test_build_envelope():
    tid = uuid4()
    env = build_event_envelope(
        event_type="payment.captured.v1",
        tenant_id=tid,
        data={"amount_minor": 100},
        correlation_id="c1",
    )
    assert is_envelope(env)
    assert env["tenantid"] == str(tid)
    assert env["data"]["amount_minor"] == 100
    assert env["correlationid"] == "c1"
    validate_envelope(env, tenant_id=tid, event_type="payment.captured.v1")


def test_validate_rejects_type_mismatch():
    tid = uuid4()
    env = build_event_envelope(
        event_type="test.a.v1", tenant_id=tid, data={}
    )
    with pytest.raises(EnvelopeValidationError, match="type_mismatch"):
        validate_envelope(env, tenant_id=tid, event_type="test.b.v1")
