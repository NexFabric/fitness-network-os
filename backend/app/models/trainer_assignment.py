from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, ForeignKeyConstraint, Index, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin


class TrainerAssignment(TenantMixin, Base):
    """Binds a trainer (login user) to a member within one tenant.

    Backs ``Scope.ASSIGNED``: without a row here a TRAINER sees no member, so
    the trainer boundary is data, not a code convention.
    """

    __tablename__ = "trainer_assignments"

    trainer_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "member_id"], ["members.tenant_id", "members.id"]
        ),
        # Partial unique: one live assignment per (tenant, trainer, member),
        # while revoked rows stay behind for audit.
        Index(
            "uq_trainer_assignments_active",
            "tenant_id",
            "trainer_user_id",
            "member_id",
            unique=True,
            postgresql_where=text("is_active"),
        ),
        Index(
            "ix_trainer_assignments_tenant_trainer",
            "tenant_id",
            "trainer_user_id",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "trainer_user_id"],
            ["staff.tenant_id", "staff.user_id"],
            name="fk_trainer_assignments_trainer_staff",
            ondelete="RESTRICT",
        ),
    )
