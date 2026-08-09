import enum
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin


class IdempotencyStatus(str, enum.Enum):
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class IdempotencyKey(Base, TenantMixin):
    """
    DEPRECATED: Legacy per-key response cache.

    Prefer IdempotencyRecord (Phase 12) for operation-scoped keys,
    request hashing, lock ownership, and terminal status.

    Table `idempotency_keys` is retained; do not drop.
    """

    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(255), index=True, nullable=False, unique=True)
    request_path: Mapped[str] = mapped_column(String(255), nullable=False)
    request_params: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IdempotencyRecord(TenantMixin, Base):
    """
    Phase 12 idempotency engine store.

    Uniqueness is (tenant_id, operation, key). request_hash detects
    payload mismatch for the same key. locked_until + owner_token
    support concurrent claim/processing.
    """

    __tablename__ = "idempotency_records"

    key: Mapped[str] = mapped_column(String(128), nullable=False)
    operation: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # sha256 hex
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=IdempotencyStatus.PROCESSING.value
    )
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String, nullable=True)
    resource_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    owner_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    _model_table_args = (
        Index(
            "ix_idempotency_records_tenant_op_key",
            "tenant_id",
            "operation",
            "key",
            unique=True,
        ),
        Index(
            "ix_idempotency_records_tenant_expires",
            "tenant_id",
            "expires_at",
        ),
    )
