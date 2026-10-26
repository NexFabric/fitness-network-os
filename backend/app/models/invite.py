"""Hashed one-time account invites (staff / member portal)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin

PURPOSE_STAFF = "staff"
PURPOSE_MEMBER_PORTAL = "member_portal"
ALLOWED_PURPOSES = frozenset({PURPOSE_STAFF, PURPOSE_MEMBER_PORTAL})


class AccountInvite(Base, TenantMixin):
    """Tenant-owned invite. Raw token is never stored — only sha256."""

    __tablename__ = "account_invites"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    _model_table_args = (
        UniqueConstraint(
            "tenant_id", "token_hash", name="uq_account_invites_tenant_token"
        ),
    )
