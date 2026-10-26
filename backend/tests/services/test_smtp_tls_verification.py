"""Unit tests for SMTP STARTTLS verified SSLContext."""

import ssl
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.notification import NotificationDelivery
from app.services.notification_providers import SmtpNotificationProvider


@pytest.mark.asyncio
async def test_smtp_starttls_passes_verified_ssl_context():
    provider = SmtpNotificationProvider()
    delivery = NotificationDelivery(
        id=uuid4(),
        tenant_id=uuid4(),
        channel="EMAIL",
        recipient_address="user@example.com",
        subject="Test Subject",
        body="Test Body",
        status="PENDING",
    )

    mock_server = MagicMock()
    mock_smtp_cls = MagicMock(return_value=mock_server)
    mock_server.__enter__.return_value = mock_server

    with (
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch.dict("os.environ", {"SMTP_PORT": "587", "SMTP_STARTTLS": "1"}),
        patch("smtplib.SMTP", mock_smtp_cls),
    ):
        result = await provider.send(delivery)

    assert result.success is True
    assert result.provider == "smtp"
    mock_smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=10)
    mock_server.starttls.assert_called_once()
    call_kwargs = mock_server.starttls.call_args.kwargs
    assert "context" in call_kwargs
    assert isinstance(call_kwargs["context"], ssl.SSLContext)
    mock_server.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_smtp_ca_bundle_loaded_into_context():
    provider = SmtpNotificationProvider()
    delivery = NotificationDelivery(
        id=uuid4(),
        tenant_id=uuid4(),
        channel="EMAIL",
        recipient_address="user@example.com",
        subject="Test Subject",
        body="Test Body",
        status="PENDING",
    )

    mock_server = MagicMock()
    mock_smtp_cls = MagicMock(return_value=mock_server)
    mock_server.__enter__.return_value = mock_server

    with (
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch.dict(
            "os.environ",
            {"SMTP_PORT": "587", "SMTP_STARTTLS": "1", "SMTP_CA_BUNDLE": "/tmp/ca.pem"},
        ),
        patch("smtplib.SMTP", mock_smtp_cls),
        patch.object(ssl.SSLContext, "load_verify_locations") as load_ca,
    ):
        result = await provider.send(delivery)

    assert result.success is True
    load_ca.assert_called_once_with(cafile="/tmp/ca.pem")
