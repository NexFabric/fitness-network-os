from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime
from app.db.base import Base, TenantMixin
from uuid import UUID
from typing import Optional
from datetime import datetime

class ConsentDefinition(TenantMixin, Base):
    __tablename__ = "consent_definitions"

    name: Mapped[str] = mapped_column(String, nullable=False)
    consent_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class ConsentVersion(TenantMixin, Base):
    __tablename__ = "consent_versions"

    definition_id: Mapped[UUID] = mapped_column(ForeignKey("consent_definitions.id"), nullable=False)
    version_number: Mapped[str] = mapped_column(String, nullable=False)
    document_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class ConsentRecord(TenantMixin, Base):
    __tablename__ = "consent_records"

    member_id: Mapped[UUID] = mapped_column(ForeignKey("members.id"), nullable=False)
    consent_type: Mapped[str] = mapped_column(String, nullable=False)
    document_version: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    given_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
