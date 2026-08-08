from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey
from uuid import UUID
from app.db.base import Base, TenantMixin
from typing import Optional

class Staff(TenantMixin, Base):
    __tablename__ = "staff"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    location_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("locations.id"), nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False, default="STAFF")
