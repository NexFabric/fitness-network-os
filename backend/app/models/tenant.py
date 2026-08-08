from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from uuid import UUID
from app.db.base import Base

class Tenant(Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    
    # Location code or branch identifier, unique per branch
    location_code: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    organization = relationship("Organization", back_populates="tenants")
