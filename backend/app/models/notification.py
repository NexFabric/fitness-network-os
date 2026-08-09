"""Phase 16 notification domain models (tenant-scoped, RLS)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin

if TYPE_CHECKING:
    from app.models.user import User


# Channel / status constants (string columns for expand-friendly schema)
CHANNEL_EMAIL = "EMAIL"
CHANNEL_SMS = "SMS"
CHANNEL_WHATSAPP = "WHATSAPP"
CHANNEL_PUSH = "PUSH"
ALLOWED_CHANNELS = frozenset(
    {CHANNEL_EMAIL, CHANNEL_SMS, CHANNEL_WHATSAPP, CHANNEL_PUSH}
)

DELIVERY_PENDING = "PENDING"
DELIVERY_QUEUED = "QUEUED"
DELIVERY_SENDING = "SENDING"
DELIVERY_SENT = "SENT"
DELIVERY_FAILED = "FAILED"
DELIVERY_DEAD = "DEAD"
DELIVERY_CANCELLED = "CANCELLED"


class NotificationTemplate(Base, TenantMixin):
    """Per-tenant template for email/SMS/WhatsApp/push body rendering."""

    __tablename__ = "notification_templates"

    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_template: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    locale: Mapped[str | None] = mapped_column(String(16), nullable=True)

    _model_table_args = (
        UniqueConstraint(
            "tenant_id", "code", name="uq_notification_templates_tenant_code"
        ),
        Index("ix_notification_templates_channel", "tenant_id", "channel"),
    )


class NotificationDelivery(Base, TenantMixin):
    """Delivery ledger row — schedule once, retry via attempt_count / available_at."""

    __tablename__ = "notification_deliveries"

    template_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    recipient_user_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    recipient_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=DELIVERY_PENDING, index=True
    )
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dedupe_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_event_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "template_id"],
            ["notification_templates.tenant_id", "notification_templates.id"],
            name="fk_notification_deliveries_template_tenant",
        ),
        # Partial unique: multiple NULL dedupe_key rows allowed (expand-friendly).
        Index(
            "uq_notification_deliveries_tenant_dedupe",
            "tenant_id",
            "dedupe_key",
            unique=True,
            postgresql_where=text("dedupe_key IS NOT NULL"),
        ),
        Index("ix_notification_deliveries_available", "status", "available_at"),
    )

    template: Mapped[NotificationTemplate | None] = relationship("NotificationTemplate")
    recipient: Mapped[User | None] = relationship("User")
