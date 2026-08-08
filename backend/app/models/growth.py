from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin


class Lead(TenantMixin, Base):
    __tablename__ = "leads"

    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="NEW")

class Opportunity(TenantMixin, Base):
    __tablename__ = "opportunities"

    lead_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "lead_id"], ["leads.tenant_id", "leads.id"]),
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
    )
    member_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    stage: Mapped[str] = mapped_column(String, nullable=False, default="PROSPECTING")
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    probability: Mapped[int | None] = mapped_column(Integer, nullable=True)

class Task(TenantMixin, Base):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_to: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    lead_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "lead_id"], ["leads.tenant_id", "leads.id"]),
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
    )
    member_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

class RetentionCockpit(TenantMixin, Base):
    __tablename__ = "retention_cockpit"

    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, unique=True)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
    )
    health_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    churn_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String, nullable=True)
