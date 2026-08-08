from uuid import UUID

from sqlalchemy import ForeignKey, ForeignKeyConstraint, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin


class Staff(TenantMixin, Base):
    __tablename__ = "staff"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    location_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "location_id"], ["locations.tenant_id", "locations.id"]),
    )
    role: Mapped[str] = mapped_column(String, nullable=False, default="STAFF")
