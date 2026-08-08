from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Float, Integer, Text, DateTime, ForeignKeyConstraint, Uuid
from app.db.base import Base, TenantMixin
from uuid import UUID
from typing import Optional
from datetime import datetime

class Lead(TenantMixin, Base):
    __tablename__ = "leads"

    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="NEW")

class Opportunity(TenantMixin, Base):
    __tablename__ = "opportunities"

    lead_id: Mapped[Optional[UUID]] = mapped_column(Uuid, nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "lead_id"], ["leads.tenant_id", "leads.id"]),
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
    )
    member_id: Mapped[Optional[UUID]] = mapped_column(Uuid, nullable=True)
    stage: Mapped[str] = mapped_column(String, nullable=False, default="PROSPECTING")
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    probability: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

class Task(TenantMixin, Base):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_to: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    lead_id: Mapped[Optional[UUID]] = mapped_column(Uuid, nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "lead_id"], ["leads.tenant_id", "leads.id"]),
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
    )
    member_id: Mapped[Optional[UUID]] = mapped_column(Uuid, nullable=True)

class RetentionCockpit(TenantMixin, Base):
    __tablename__ = "retention_cockpit"

    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, unique=True)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
    )
    health_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    churn_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String, nullable=True)
