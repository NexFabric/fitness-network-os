from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin


class BillingAccount(TenantMixin, Base):
    __tablename__ = "billing_accounts"

    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    member_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    
    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
    )

    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="billing_account")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="billing_account")

class Invoice(TenantMixin, Base):
    __tablename__ = "invoices"

    billing_account_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="OPEN") # DRAFT, OPEN, PAID, VOID
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    total_amount_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "billing_account_id"], ["billing_accounts.tenant_id", "billing_accounts.id"]),
    )

    billing_account: Mapped["BillingAccount"] = relationship("BillingAccount", back_populates="invoices")
    items: Mapped[list["InvoiceItem"]] = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    allocations: Mapped[list["PaymentAllocation"]] = relationship("PaymentAllocation", back_populates="invoice")

class InvoiceItem(TenantMixin, Base):
    __tablename__ = "invoice_items"

    invoice_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "invoice_id"], ["invoices.tenant_id", "invoices.id"]),
    )

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")

class Payment(TenantMixin, Base):
    __tablename__ = "payments"

    billing_account_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    status: Mapped[str] = mapped_column(String, nullable=False, default="SUCCEEDED")
    method: Mapped[str] = mapped_column(String, nullable=False) # e.g. CREDIT_CARD, CASH, TRANSFER

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "billing_account_id"], ["billing_accounts.tenant_id", "billing_accounts.id"]),
    )

    billing_account: Mapped["BillingAccount"] = relationship("BillingAccount", back_populates="payments")
    allocations: Mapped[list["PaymentAllocation"]] = relationship("PaymentAllocation", back_populates="payment")

class PaymentAllocation(TenantMixin, Base):
    __tablename__ = "payment_allocations"

    payment_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    invoice_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "payment_id"], ["payments.tenant_id", "payments.id"]),
        ForeignKeyConstraint(["tenant_id", "invoice_id"], ["invoices.tenant_id", "invoices.id"]),
    )

    payment: Mapped["Payment"] = relationship("Payment", back_populates="allocations")
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="allocations")
