"""Notification transport adapters (Phase 16C / P1-8).

Domain never calls WhatsApp/Email SDKs directly — adapters only.
LogNotificationProvider is a silent no-network stub.
ConsoleEmailNotificationProvider is the default EMAIL adapter: structured
console logs only (no SMTP / network). Real SMTP stays deferred and must
be env-gated + default-off when added.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from app.models.notification import NotificationDelivery

logger = logging.getLogger(__name__)

# Env override: log | console (default console for EMAIL channel).
# Real SMTP must not be introduced without a separate gated provider.
_EMAIL_PROVIDER_ENV = "NOTIFICATION_EMAIL_PROVIDER"


@dataclass(frozen=True)
class ProviderResult:
    success: bool
    provider: str
    provider_message_id: str | None = None
    error: str | None = None


class NotificationProvider(Protocol):
    name: str

    async def send(self, delivery: NotificationDelivery) -> ProviderResult: ...


class LogNotificationProvider:
    """Dev/test provider: always succeeds, no external calls, no log noise."""

    name = "log"

    async def send(self, delivery: NotificationDelivery) -> ProviderResult:
        mid = f"log-{delivery.id.hex[:12]}-{uuid4().hex[:8]}"
        return ProviderResult(success=True, provider=self.name, provider_message_id=mid)


class ConsoleEmailNotificationProvider:
    """EMAIL adapter: structured console log only — never network SMTP.

    Logs delivery metadata only (ids, channel, recipient address, template_id,
    subject key/text if short). Does **not** log free-form body content
    (may contain OTP/secrets/PII). Never logs PAN/CVV/card data.
    """

    name = "console_email"

    async def send(self, delivery: NotificationDelivery) -> ProviderResult:
        mid = f"console-email-{delivery.id.hex[:12]}-{uuid4().hex[:8]}"
        # Structured fields only — omit body / context (sensitive free-form).
        logger.info(
            "notification.email.console delivery_id=%s channel=%s "
            "recipient_address=%s template_id=%s subject=%s "
            "provider_message_id=%s",
            delivery.id,
            delivery.channel,
            delivery.recipient_address,
            delivery.template_id,
            delivery.subject,
            mid,
        )
        return ProviderResult(success=True, provider=self.name, provider_message_id=mid)


class FailingNotificationProvider:
    """Test helper: always fails."""

    name = "fail"

    async def send(self, delivery: NotificationDelivery) -> ProviderResult:
        return ProviderResult(
            success=False,
            provider=self.name,
            error="provider_forced_failure",
        )


def _email_provider() -> NotificationProvider:
    """Resolve EMAIL channel adapter.

    NOTIFICATION_EMAIL_PROVIDER=log|console (default: console).
    Unknown values fall back to console (safe, no network).
    """
    mode = os.environ.get(_EMAIL_PROVIDER_ENV, "console").strip().lower()
    if mode == "log":
        return LogNotificationProvider()
    return ConsoleEmailNotificationProvider()


def default_providers() -> dict[str, NotificationProvider]:
    log = LogNotificationProvider()
    return {
        "EMAIL": _email_provider(),
        "SMS": log,
        "WHATSAPP": log,
        "PUSH": log,
    }
