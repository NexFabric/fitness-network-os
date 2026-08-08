from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, JSON, Text
from typing import Any, Dict, Optional

from app.db.base import Base, TenantMixin

class OutboxEvent(Base, TenantMixin):
    """
    Transactional Outbox pattern for publishing events reliably.
    ADR-038 Outbox Pattern
    """
    __tablename__ = "outbox_events"

    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING", index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class InboxEvent(Base, TenantMixin):
    """
    Transactional Inbox pattern for processing incoming webhooks/events exactly once.
    ADR-038 Inbox Pattern
    """
    __tablename__ = "inbox_events"

    event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING", index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
