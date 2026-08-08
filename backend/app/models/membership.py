from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Integer, Boolean, DateTime, ForeignKeyConstraint, Uuid
from app.db.base import Base, TenantMixin
from uuid import UUID
from typing import Optional, List
from datetime import datetime

class Plan(TenantMixin, Base):
    __tablename__ = "plans"

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class PlanVersion(TenantMixin, Base):
    __tablename__ = "plan_versions"

    plan_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "plan_id"], ["plans.tenant_id", "plans.id"]),
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    price_amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    billing_cycle_months: Mapped[int] = mapped_column(Integer, nullable=False)

class Membership(TenantMixin, Base):
    __tablename__ = "memberships"

    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    plan_version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
        ForeignKeyConstraint(["tenant_id", "plan_version_id"], ["plan_versions.tenant_id", "plan_versions.id"]),
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="ACTIVE")
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class Entitlement(TenantMixin, Base):
    __tablename__ = "entitlements"

    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    membership_id: Mapped[Optional[UUID]] = mapped_column(Uuid, nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
        ForeignKeyConstraint(["tenant_id", "membership_id"], ["memberships.tenant_id", "memberships.id"]),
    )
    entitlement_type: Mapped[str] = mapped_column(String, nullable=False)
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
