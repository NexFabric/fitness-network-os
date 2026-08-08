from uuid import UUID, uuid4
from datetime import datetime, UTC
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy import DateTime, Uuid, UniqueConstraint

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

    @declared_attr
    def __table_args__(cls):
        uq = UniqueConstraint('tenant_id', 'id', name=f"uq_{cls.__tablename__}_tenant_id")
        # Check if the class defines its own __table_args__ outside of this mixin
        if hasattr(cls, '_model_table_args'):
            args = cls._model_table_args
            if isinstance(args, tuple):
                return args + (uq,)
            elif isinstance(args, dict):
                args_copy = args.copy()
                # we don't handle dict nicely here if we return tuple, just return tuple
                pass 
        return (uq,)

