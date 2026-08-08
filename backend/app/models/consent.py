from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKeyConstraint, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin


class ConsentDefinition(TenantMixin, Base):
    __tablename__ = "consent_definitions"

    name: Mapped[str] = mapped_column(String, nullable=False)
    consent_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

class ConsentVersion(TenantMixin, Base):
    __tablename__ = "consent_versions"

    definition_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "definition_id"], ["consent_definitions.tenant_id", "consent_definitions.id"]),
    )
    version_number: Mapped[str] = mapped_column(String, nullable=False)
    document_url: Mapped[str | None] = mapped_column(String, nullable=True)

class ConsentRecord(TenantMixin, Base):
    __tablename__ = "consent_records"

    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
    )
    consent_type: Mapped[str] = mapped_column(String, nullable=False)
    document_version: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    given_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
