"""Phase 16 report domain models (tenant-scoped, RLS)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
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

REPORT_STATUS_PENDING = "PENDING"
REPORT_STATUS_RUNNING = "RUNNING"
REPORT_STATUS_SUCCEEDED = "SUCCEEDED"
REPORT_STATUS_FAILED = "FAILED"
REPORT_STATUS_CANCELLED = "CANCELLED"


class ReportDefinition(Base, TenantMixin):
    """Named report configuration for a tenant."""

    __tablename__ = "report_definitions"

    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_type: Mapped[str] = mapped_column(
        String(100), nullable=False, default="GENERIC"
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    _model_table_args = (
        UniqueConstraint("tenant_id", "code", name="uq_report_definitions_tenant_code"),
    )

    runs: Mapped[list[ReportRun]] = relationship(
        "ReportRun", back_populates="definition", cascade="all, delete-orphan"
    )


class ReportRun(Base, TenantMixin):
    """Async report execution record (export metadata; not the export blob)."""

    __tablename__ = "report_runs"

    definition_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    # Index via _model_table_args (ix_report_runs_status on tenant_id, status).
    # Do not set index=True here — same auto name collides with the composite Index.
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=REPORT_STATUS_PENDING
    )
    result_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    export_format: Mapped[str | None] = mapped_column(String(32), nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    requested_by_user_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "definition_id"],
            ["report_definitions.tenant_id", "report_definitions.id"],
            name="fk_report_runs_definition_tenant",
        ),
        # Partial unique: multiple NULL dedupe_key rows allowed.
        Index(
            "uq_report_runs_tenant_dedupe",
            "tenant_id",
            "dedupe_key",
            unique=True,
            postgresql_where=text("dedupe_key IS NOT NULL"),
        ),
        Index("ix_report_runs_status", "tenant_id", "status"),
    )

    definition: Mapped[ReportDefinition] = relationship(
        "ReportDefinition", back_populates="runs"
    )
