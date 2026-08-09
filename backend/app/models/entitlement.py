import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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


class EntitlementTransactionType(str, enum.Enum):
    ALLOCATE = "ALLOCATE"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    CONSUME = "CONSUME"
    ADJUST = "ADJUST"
    EXPIRE = "EXPIRE"
    REVERSE = "REVERSE"


class MembershipEntitlementStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class EntitlementDefinition(TenantMixin, Base):
    """Tenant catalog of grantable entitlement rights."""

    __tablename__ = "entitlement_definitions"

    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[EntitlementType] = mapped_column(Enum(EntitlementType), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    _model_table_args = (
        Index("ix_entitlement_def_tenant_code", "tenant_id", "code", unique=True),
    )


class PlanEntitlement(TenantMixin, Base):
    """Immutable plan-version mapping of entitlement grants."""

    __tablename__ = "plan_entitlements"

    plan_version_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    entitlement_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unlimited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "plan_version_id"],
            ["plan_versions.tenant_id", "plan_versions.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "entitlement_id"],
            ["entitlement_definitions.tenant_id", "entitlement_definitions.id"],
            ondelete="CASCADE",
        ),
        Index(
            "ix_plan_entit_tenant_pv_entit",
            "tenant_id",
            "plan_version_id",
            "entitlement_id",
            unique=True,
        ),
        CheckConstraint("quantity >= 0", name="ck_plan_entitlements_quantity_nonneg"),
    )


class MembershipEntitlement(TenantMixin, Base):
    """Concrete membership-scoped entitlement snapshot."""

    __tablename__ = "membership_entitlements"

    membership_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    entitlement_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    source_plan_version_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    granted_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unlimited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=MembershipEntitlementStatus.ACTIVE.value
    )

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
        ForeignKeyConstraint(
            ["tenant_id", "source_plan_version_id"],
            ["plan_versions.tenant_id", "plan_versions.id"],
            ondelete="SET NULL",
        ),
        Index(
            "ix_memb_entit_tenant_memb_entit",
            "tenant_id",
            "membership_id",
            "entitlement_id",
            unique=True,
        ),
        CheckConstraint(
            "granted_quantity >= 0", name="ck_membership_entitlements_granted_nonneg"
        ),
    )


class EntitlementWallet(TenantMixin, Base):
    """Authoritative balance for count-based (and boolean) rights."""

    __tablename__ = "entitlement_wallets"

    member_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    membership_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    membership_entitlement_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
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
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "membership_entitlement_id"],
            ["membership_entitlements.tenant_id", "membership_entitlements.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "entitlement_id"],
            ["entitlement_definitions.tenant_id", "entitlement_definitions.id"],
            ondelete="CASCADE",
        ),
        Index(
            "ix_entit_wallets_tenant_me",
            "tenant_id",
            "membership_entitlement_id",
            unique=True,
        ),
        Index(
            "ix_entit_wallets_tenant_memb_entit",
            "tenant_id",
            "membership_id",
            "entitlement_id",
            unique=True,
        ),
        CheckConstraint("allocated >= 0", name="ck_entitlement_wallets_allocated_nonneg"),
        CheckConstraint("reserved >= 0", name="ck_entitlement_wallets_reserved_nonneg"),
        CheckConstraint("consumed >= 0", name="ck_entitlement_wallets_consumed_nonneg"),
        CheckConstraint("remaining >= 0", name="ck_entitlement_wallets_remaining_nonneg"),
    )


class EntitlementTransaction(TenantMixin, Base):
    """Append-only entitlement ledger."""

    __tablename__ = "entitlement_transactions"

    wallet_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    membership_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    entitlement_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    transaction_type: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    balance_before: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "wallet_id"],
            ["entitlement_wallets.tenant_id", "entitlement_wallets.id"],
            ondelete="CASCADE",
        ),
        Index("ix_entit_tx_tenant_idem_key", "tenant_id", "idempotency_key", unique=True),
        Index("ix_entit_tx_tenant_wallet", "tenant_id", "wallet_id"),
    )
