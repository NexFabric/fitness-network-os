from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin


class OutboxEvent(TenantMixin, Base):
    """Transactional Outbox — durable publish buffer (ADR-020).

    Delivery is at-least-once; consumers must be idempotent for effectively-once
    business effects (do not claim global exactly-once).
    """

    __tablename__ = "outbox_events"

    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PENDING", index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    aggregate_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aggregate_id: Mapped[UUID | None] = mapped_column(nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    _model_table_args = (
        UniqueConstraint(
            "tenant_id", "dedupe_key", name="uq_outbox_events_tenant_dedupe"
        ),
        Index("ix_outbox_events_available", "status", "available_at"),
        Index("ix_outbox_events_lease", "status", "lease_until"),
    )


class InboxEvent(TenantMixin, Base):
    """Transactional Inbox — deduplicated intake for external events.

    At-least-once receive + UNIQUE(tenant_id, event_id) + retryable handlers.
    """

    __tablename__ = "inbox_events"

    event_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PENDING", index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    available_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    _model_table_args = (
        UniqueConstraint(
            "tenant_id", "event_id", name="uq_inbox_events_tenant_event_id"
        ),
        Index("ix_inbox_events_available", "status", "available_at"),
    )
