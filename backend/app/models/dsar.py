"""KVKK data-subject request ledger (tenant-owned)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin

KIND_EXPORT = "EXPORT"
KIND_ERASURE = "ERASURE"
ALLOWED_KINDS = frozenset({KIND_EXPORT, KIND_ERASURE})

STATUS_RECEIVED = "RECEIVED"
STATUS_PACKAGED = "PACKAGED"
STATUS_DELIVERED = "DELIVERED"
STATUS_REJECTED = "REJECTED"
STATUS_COMPLETED = "COMPLETED"
ALLOWED_STATUSES = frozenset(
    {
        STATUS_RECEIVED,
        STATUS_PACKAGED,
        STATUS_DELIVERED,
        STATUS_REJECTED,
        STATUS_COMPLETED,
    }
)


class DsarRequest(Base, TenantMixin):
    __tablename__ = "dsar_requests"

    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    requested_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    package_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(128), nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "member_id"],
            ["members.tenant_id", "members.id"],
            name="fk_dsar_requests_member_tenant",
        ),
        Index(
            "ix_dsar_requests_tenant_dedupe",
            "tenant_id",
            "dedupe_key",
            unique=True,
            postgresql_where=text("dedupe_key IS NOT NULL"),
        ),
    )
