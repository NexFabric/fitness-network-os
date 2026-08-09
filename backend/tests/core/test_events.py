"""Event envelope unit tests."""

from uuid import uuid4

from app.core.events import build_event_envelope, is_envelope


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
