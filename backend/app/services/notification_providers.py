"""Notification transport adapters (Phase 16C).

Domain never calls WhatsApp/Email SDKs directly — adapters only.
Default LogNotificationProvider records provider_message_id without network I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from app.models.notification import NotificationDelivery


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
    """Dev/test provider: always succeeds, no external calls."""

    name = "log"

    async def send(self, delivery: NotificationDelivery) -> ProviderResult:
        mid = f"log-{delivery.id.hex[:12]}-{uuid4().hex[:8]}"
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


def default_providers() -> dict[str, NotificationProvider]:
    log = LogNotificationProvider()
    return {
        "EMAIL": log,
        "SMS": log,
        "WHATSAPP": log,
        "PUSH": log,
    }
