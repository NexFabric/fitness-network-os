import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BreakGlassStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class BreakGlassSession(Base):
    """Time-limited emergency access session.

    NOT tenant-scoped: this is a platform-level emergency tool.
    Each session grants temporary elevated access to a specific tenant
    and auto-expires after the configured duration.
    """

    __tablename__ = "break_glass_sessions"

    actor_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    target_tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    ticket_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BreakGlassStatus.ACTIVE.value
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actions_taken: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'EXPIRED', 'REVOKED')",
            name="ck_break_glass_sessions_status",
        ),
        Index("ix_break_glass_active", "status", "expires_at"),
    )
