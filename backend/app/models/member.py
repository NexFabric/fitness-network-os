from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from app.db.base import Base, TenantMixin
from uuid import UUID
from typing import Optional

class Member(TenantMixin, Base):
    __tablename__ = "members"

    member_number: Mapped[str] = mapped_column(String, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="LEAD")

class Tag(TenantMixin, Base):
    __tablename__ = "member_tags"

    member_id: Mapped[UUID] = mapped_column(ForeignKey("members.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

class Note(TenantMixin, Base):
    __tablename__ = "member_notes"

    member_id: Mapped[UUID] = mapped_column(ForeignKey("members.id"), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
