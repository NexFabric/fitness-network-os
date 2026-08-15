import enum
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    VOID = "VOID"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    REFUNDED = "REFUNDED"


class RefundStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class CreditNoteStatus(str, enum.Enum):
    OPEN = "OPEN"
    FULLY_APPLIED = "FULLY_APPLIED"
    VOID = "VOID"


class ReconciliationStatus(str, enum.Enum):
    OPEN = "OPEN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ReconciliationItemStatus(str, enum.Enum):
    UNMATCHED = "UNMATCHED"
    MATCHED = "MATCHED"
    DISPUTED = "DISPUTED"


class BillingAccount(TenantMixin, Base):
    __tablename__ = "billing_accounts"

    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    member_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    status: Mapped[str] = mapped_column(String, nullable=False, default="ACTIVE")

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "member_id"], ["members.tenant_id", "members.id"]
        ),
        Index(
            "ix_billing_accounts_tenant_member",
            "tenant_id",
            "member_id",
            unique=True,
            postgresql_where=text("member_id IS NOT NULL"),
        ),
    )

    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="billing_account"
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="billing_account"
    )


class Invoice(TenantMixin, Base):
    __tablename__ = "invoices"

    billing_account_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    membership_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    invoice_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=InvoiceStatus.DRAFT.value
    )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    issued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    voided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    total_amount_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    paid_amount_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discount_amount_minor: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "billing_account_id"],
            ["billing_accounts.tenant_id", "billing_accounts.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
        ),
        CheckConstraint("total_amount_minor >= 0", name="ck_invoices_total_nonneg"),
        CheckConstraint("paid_amount_minor >= 0", name="ck_invoices_paid_nonneg"),
        CheckConstraint(
            "discount_amount_minor >= 0", name="ck_invoices_discount_nonneg"
        ),
        CheckConstraint(
            "paid_amount_minor <= total_amount_minor",
            name="ck_invoices_paid_lte_total",
        ),
        Index(
            "ix_invoices_tenant_idem",
            "tenant_id",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
        Index(
            "ix_invoices_tenant_number",
            "tenant_id",
            "invoice_number",
            unique=True,
            postgresql_where=text("invoice_number IS NOT NULL"),
        ),
    )

    billing_account: Mapped["BillingAccount"] = relationship(
        "BillingAccount", back_populates="invoices"
    )
    items: Mapped[list["InvoiceItem"]] = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )
    allocations: Mapped[list["PaymentAllocation"]] = relationship(
        "PaymentAllocation", back_populates="invoice"
    )


class InvoiceItem(TenantMixin, Base):
    __tablename__ = "invoice_items"

    invoice_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    unit_amount_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "invoice_id"], ["invoices.tenant_id", "invoices.id"]
        ),
        CheckConstraint("quantity > 0", name="ck_invoice_items_qty_pos"),
        CheckConstraint("amount_minor >= 0", name="ck_invoice_items_amount_nonneg"),
        CheckConstraint("unit_amount_minor >= 0", name="ck_invoice_items_unit_nonneg"),
    )

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")


class Payment(TenantMixin, Base):
    __tablename__ = "payments"

    billing_account_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    refunded_amount_minor: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=PaymentStatus.SUCCEEDED.value
    )
    method: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "billing_account_id"],
            ["billing_accounts.tenant_id", "billing_accounts.id"],
        ),
        CheckConstraint("amount_minor > 0", name="ck_payments_amount_pos"),
        CheckConstraint(
            "refunded_amount_minor >= 0", name="ck_payments_refunded_nonneg"
        ),
        CheckConstraint(
            "refunded_amount_minor <= amount_minor",
            name="ck_payments_refunded_lte_amount",
        ),
        Index(
            "ix_payments_tenant_idem",
            "tenant_id",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
    )

    billing_account: Mapped["BillingAccount"] = relationship(
        "BillingAccount", back_populates="payments"
    )
    allocations: Mapped[list["PaymentAllocation"]] = relationship(
        "PaymentAllocation",
        back_populates="payment",
        overlaps="allocations",
    )


class PaymentAllocation(TenantMixin, Base):
    """Immutable payment→invoice allocation. Never mutate amount; reverse via reversals."""

    __tablename__ = "payment_allocations"

    payment_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    invoice_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "payment_id"], ["payments.tenant_id", "payments.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "invoice_id"], ["invoices.tenant_id", "invoices.id"]
        ),
        CheckConstraint("amount_minor > 0", name="ck_payment_allocations_amount_pos"),
    )

    payment: Mapped["Payment"] = relationship(
        "Payment", back_populates="allocations", overlaps="allocations"
    )
    invoice: Mapped["Invoice"] = relationship(
        "Invoice", back_populates="allocations", overlaps="allocations,payment"
    )
    reversals: Mapped[list["PaymentAllocationReversal"]] = relationship(
        "PaymentAllocationReversal",
        back_populates="allocation",
        overlaps="allocation",
    )


class PaymentAllocationReversal(TenantMixin, Base):
    """Append-only reversal of a payment allocation (refund unwind)."""

    __tablename__ = "payment_allocation_reversals"

    allocation_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    refund_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "allocation_id"],
            ["payment_allocations.tenant_id", "payment_allocations.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "refund_id"],
            ["refunds.tenant_id", "refunds.id"],
        ),
        CheckConstraint(
            "amount_minor > 0", name="ck_payment_allocation_reversals_amount_pos"
        ),
    )

    allocation: Mapped["PaymentAllocation"] = relationship(
        "PaymentAllocation",
        back_populates="reversals",
        overlaps="reversals",
    )


class Refund(TenantMixin, Base):
    __tablename__ = "refunds"

    payment_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=RefundStatus.SUCCEEDED.value
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "payment_id"], ["payments.tenant_id", "payments.id"]
        ),
        CheckConstraint("amount_minor > 0", name="ck_refunds_amount_pos"),
        Index("ix_refunds_tenant_idem", "tenant_id", "idempotency_key", unique=True),
    )


class CreditNote(TenantMixin, Base):
    """Account-level credit that can be applied to invoices."""

    __tablename__ = "credit_notes"

    billing_account_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=CreditNoteStatus.OPEN.value
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "billing_account_id"],
            ["billing_accounts.tenant_id", "billing_accounts.id"],
        ),
        CheckConstraint("amount_minor > 0", name="ck_credit_notes_amount_pos"),
        CheckConstraint(
            "remaining_minor >= 0", name="ck_credit_notes_remaining_nonneg"
        ),
        CheckConstraint(
            "remaining_minor <= amount_minor",
            name="ck_credit_notes_remaining_lte_amount",
        ),
        Index(
            "ix_credit_notes_tenant_idem",
            "tenant_id",
            "idempotency_key",
            unique=True,
        ),
    )


class CreditApplication(TenantMixin, Base):
    __tablename__ = "credit_applications"

    credit_note_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    invoice_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "credit_note_id"],
            ["credit_notes.tenant_id", "credit_notes.id"],
        ),
        ForeignKeyConstraint(
            ["tenant_id", "invoice_id"], ["invoices.tenant_id", "invoices.id"]
        ),
        CheckConstraint("amount_minor > 0", name="ck_credit_applications_amount_pos"),
    )


class Discount(TenantMixin, Base):
    """Tenant discount catalog (fixed amount or basis-points percent)."""

    __tablename__ = "discounts"

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    amount_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    percent_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    _model_table_args = (
        Index("ix_discounts_tenant_code", "tenant_id", "code", unique=True),
        CheckConstraint(
            "(amount_minor IS NOT NULL AND percent_bps IS NULL) OR "
            "(amount_minor IS NULL AND percent_bps IS NOT NULL)",
            name="ck_discounts_fixed_or_percent",
        ),
        CheckConstraint(
            "amount_minor IS NULL OR amount_minor >= 0",
            name="ck_discounts_amount_nonneg",
        ),
        CheckConstraint(
            "percent_bps IS NULL OR (percent_bps >= 0 AND percent_bps <= 10000)",
            name="ck_discounts_percent_bps_range",
        ),
    )


class InvoiceDiscount(TenantMixin, Base):
    __tablename__ = "invoice_discounts"

    invoice_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    discount_id: Mapped[UUID | None] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "invoice_id"], ["invoices.tenant_id", "invoices.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "discount_id"], ["discounts.tenant_id", "discounts.id"]
        ),
        CheckConstraint("amount_minor > 0", name="ck_invoice_discounts_amount_pos"),
    )


class ReconciliationRun(TenantMixin, Base):
    __tablename__ = "reconciliation_runs"

    status: Mapped[str] = mapped_column(
        String, nullable=False, default=ReconciliationStatus.OPEN.value
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actor_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)


class ReconciliationItem(TenantMixin, Base):
    __tablename__ = "reconciliation_items"

    run_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    external_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=ReconciliationItemStatus.UNMATCHED.value
    )
    matched_payment_id: Mapped[UUID | None] = mapped_column(nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "run_id"],
            ["reconciliation_runs.tenant_id", "reconciliation_runs.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "matched_payment_id"],
            ["payments.tenant_id", "payments.id"],
        ),
        CheckConstraint("amount_minor != 0", name="ck_recon_items_amount_nonzero"),
    )


class PaymentAttemptStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class PaymentAttempt(TenantMixin, Base):
    __tablename__ = "payment_attempts"

    invoice_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    billing_account_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PaymentAttemptStatus.PENDING.value
    )
    gateway_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gateway_attempt_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "invoice_id"], ["invoices.tenant_id", "invoices.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "billing_account_id"],
            ["billing_accounts.tenant_id", "billing_accounts.id"],
        ),
    )


class DunningPolicy(TenantMixin, Base):
    __tablename__ = "dunning_policies"

    name: Mapped[str] = mapped_column(
        String(100), nullable=False, default="Default Dunning"
    )
    grace_period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    max_retry_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    retry_interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    block_access_on_failure: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
