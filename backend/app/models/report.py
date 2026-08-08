from typing import Any
from uuid import UUID

from sqlalchemy import JSON, ForeignKeyConstraint, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin


class ReportDefinition(Base, TenantMixin):
    """
    Defines a report template or query configuration.
    """
    __tablename__ = "report_definitions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    runs: Mapped[list["ReportRun"]] = relationship("ReportRun", back_populates="definition", cascade="all, delete-orphan")


class ReportRun(Base, TenantMixin):
    """
    Tracks the execution of a ReportDefinition.
    """
    __tablename__ = "report_runs"

    definition_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "definition_id"], ["report_definitions.tenant_id", "report_definitions.id"]),
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    result_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    definition: Mapped["ReportDefinition"] = relationship("ReportDefinition", back_populates="runs")
