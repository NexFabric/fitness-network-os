from uuid import UUID, uuid4
from datetime import datetime, UTC
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy import DateTime, Uuid

class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

class TenantMixin:
    """Mixin for models that belong to a specific tenant."""
    @declared_attr
    def tenant_id(cls) -> Mapped[UUID]:
        return mapped_column(Uuid, nullable=False, index=True)
