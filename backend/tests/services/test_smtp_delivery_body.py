"""SMTP must send the ledger body, not only context['body']."""

from types import SimpleNamespace

from app.services.notification_providers import _delivery_body


def test_delivery_body_prefers_ledger_column():
    delivery = SimpleNamespace(
        body="Rendered template body",
        context={"body": "stale context body"},
    )
    assert _delivery_body(delivery) == "Rendered template body"


def test_delivery_body_falls_back_to_context():
    delivery = SimpleNamespace(body=None, context={"body": "from context"})
    assert _delivery_body(delivery) == "from context"


def test_delivery_body_generic_when_empty():
    delivery = SimpleNamespace(body="  ", context={})
    assert _delivery_body(delivery) == "Size yeni bir mesajımız var."
