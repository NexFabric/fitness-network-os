"""Growth CRM tables are schema-only.

There is no public API. Do not add endpoints or drop these tables: they carry
tenant_id + RLS and the money-int / RLS tests. Expand only with a product
decision and an ADR.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
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
        ForeignKeyConstraint(
            ["tenant_id", "member_id"], ["members.tenant_id", "members.id"]
        ),
        CheckConstraint(
            "value_amount_minor IS NULL OR value_amount_minor >= 0",
            name="ck_opportunities_value_amount_minor_nonneg",
        ),
    )
    member_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    stage: Mapped[str] = mapped_column(String, nullable=False, default="PROSPECTING")
    # Money: integer minor units only (no float)
    value_amount_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    probability: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Task(TenantMixin, Base):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    assigned_to: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    lead_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "lead_id"], ["leads.tenant_id", "leads.id"]),
        ForeignKeyConstraint(
            ["tenant_id", "member_id"], ["members.tenant_id", "members.id"]
        ),
    )
    member_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)


class RetentionCockpit(TenantMixin, Base):
    __tablename__ = "retention_cockpit"

    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, unique=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "member_id"], ["members.tenant_id", "members.id"]
        ),
        CheckConstraint(
            "churn_probability_bps IS NULL OR "
            "(churn_probability_bps >= 0 AND churn_probability_bps <= 10000)",
            name="ck_retention_churn_bps_range",
        ),
    )
    health_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Non-money analytics: store basis points 0..10000 (e.g. 1250 = 12.50%)
    churn_probability_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_calculated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    risk_level: Mapped[str | None] = mapped_column(String, nullable=True)
