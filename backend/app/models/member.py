from uuid import UUID

from sqlalchemy import ForeignKeyConstraint, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin


class Member(TenantMixin, Base):
    __tablename__ = "members"

    member_number: Mapped[str] = mapped_column(String, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="LEAD")

class Tag(TenantMixin, Base):
    __tablename__ = "member_tags"

    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
    )
    name: Mapped[str] = mapped_column(String, nullable=False)

class Note(TenantMixin, Base):
    __tablename__ = "member_notes"

    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
    )
    content: Mapped[str] = mapped_column(String, nullable=False)
