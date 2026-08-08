from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, unique=True, nullable=True)

    # One Organization has many Tenants
    tenants = relationship("Tenant", back_populates="organization", cascade="all, delete-orphan")
