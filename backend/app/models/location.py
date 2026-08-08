from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from app.db.base import Base, TenantMixin

class Location(TenantMixin, Base):
    __tablename__ = "locations"

    name: Mapped[str] = mapped_column(String, nullable=False)
    timezone: Mapped[str] = mapped_column(String, nullable=False, default="UTC")
    address: Mapped[str] = mapped_column(String, nullable=True)
