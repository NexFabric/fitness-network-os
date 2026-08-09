import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin


class EntitlementType(str, enum.Enum):
    COUNT = "COUNT"
    BOOLEAN = "BOOLEAN"


class EntitlementDefinition(TenantMixin, Base):
    __tablename__ = "entitlement_definitions"

    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[EntitlementType] = mapped_column(Enum(EntitlementType), nullable=False)

    _model_table_args = (
        Index("ix_entitlement_def_tenant_code", "tenant_id", "code", unique=True),
    )


class PlanEntitlement(TenantMixin, Base):
    __tablename__ = "plan_entitlements"

    plan_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    entitlement_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "plan_id"],
            ["plans.tenant_id", "plans.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "entitlement_id"],
            ["entitlement_definitions.tenant_id", "entitlement_definitions.id"],
            ondelete="CASCADE",
        ),
        Index("ix_plan_entit_tenant_plan_entit", "tenant_id", "plan_id", "entitlement_id", unique=True),
    )


class MembershipEntitlement(TenantMixin, Base):
    __tablename__ = "membership_entitlements"

    membership_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    entitlement_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "entitlement_id"],
            ["entitlement_definitions.tenant_id", "entitlement_definitions.id"],
            ondelete="CASCADE",
        ),
        Index("ix_memb_entit_tenant_memb_entit", "tenant_id", "membership_id", "entitlement_id", unique=True),
    )


class EntitlementWallet(TenantMixin, Base):
    __tablename__ = "entitlement_wallets"

    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    entitlement_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    
    allocated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consumed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    remaining: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "member_id"],
            ["members.tenant_id", "members.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "entitlement_id"],
            ["entitlement_definitions.tenant_id", "entitlement_definitions.id"],
            ondelete="CASCADE",
        ),
        Index("ix_entit_wallets_tenant_memb_entit", "tenant_id", "member_id", "entitlement_id", unique=True),
    )


class EntitlementTransaction(TenantMixin, Base):
    __tablename__ = "entitlement_transactions"

    wallet_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "wallet_id"],
            ["entitlement_wallets.tenant_id", "entitlement_wallets.id"],
            ondelete="CASCADE",
        ),
        Index("ix_entit_tx_tenant_idem_key", "tenant_id", "idempotency_key", unique=True),
    )
