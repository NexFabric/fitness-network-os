from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin


class PassportConfig(Base, TenantMixin):
    """
    Tenant-owned. Defines rules for how this gym (tenant) participates in the Federation Passport.
    """

    __tablename__ = "passport_configs"

    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allowed_home_gym_tiers: Mapped[str | None] = mapped_column(String, nullable=True)
    rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ComplianceRecord(Base, TenantMixin):
    """
    Tenant-owned. Tracks gym certifications and audit results at the Federation level.
    """

    __tablename__ = "compliance_records"

    certification_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    audit_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    auditor_notes: Mapped[str | None] = mapped_column(String, nullable=True)


class NetworkAlert(Base):
    """
    Organization-owned. Broadcasts messages from the Federation (Organization) to specific or all tenants.
    """

    __tablename__ = "network_alerts"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    target_tenant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tenants.id"), nullable=True
    )

    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False, default="INFO")
