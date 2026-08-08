from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Integer, Boolean, DateTime
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

    plan_id: Mapped[UUID] = mapped_column(ForeignKey("plans.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    price_amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    billing_cycle_months: Mapped[int] = mapped_column(Integer, nullable=False)

class Membership(TenantMixin, Base):
    __tablename__ = "memberships"

    member_id: Mapped[UUID] = mapped_column(ForeignKey("members.id"), nullable=False)
    plan_version_id: Mapped[UUID] = mapped_column(ForeignKey("plan_versions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ACTIVE")
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class Entitlement(TenantMixin, Base):
    __tablename__ = "entitlements"

    member_id: Mapped[UUID] = mapped_column(ForeignKey("members.id"), nullable=False)
    membership_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("memberships.id"), nullable=True)
    entitlement_type: Mapped[str] = mapped_column(String, nullable=False)
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
