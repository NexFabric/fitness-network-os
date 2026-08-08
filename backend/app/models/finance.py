from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime
from app.db.base import Base, TenantMixin
from uuid import UUID
from typing import Optional, List
from datetime import datetime

class BillingAccount(TenantMixin, Base):
    __tablename__ = "billing_accounts"

    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    member_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("members.id"), nullable=True, index=True)
    
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="billing_account")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="billing_account")

class Invoice(TenantMixin, Base):
    __tablename__ = "invoices"

    billing_account_id: Mapped[UUID] = mapped_column(ForeignKey("billing_accounts.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="OPEN") # DRAFT, OPEN, PAID, VOID
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    total_amount_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    billing_account: Mapped["BillingAccount"] = relationship("BillingAccount", back_populates="invoices")
    items: Mapped[List["InvoiceItem"]] = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    allocations: Mapped[List["PaymentAllocation"]] = relationship("PaymentAllocation", back_populates="invoice")

class InvoiceItem(TenantMixin, Base):
    __tablename__ = "invoice_items"

    invoice_id: Mapped[UUID] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")

class Payment(TenantMixin, Base):
    __tablename__ = "payments"

    billing_account_id: Mapped[UUID] = mapped_column(ForeignKey("billing_accounts.id"), nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    status: Mapped[str] = mapped_column(String, nullable=False, default="SUCCEEDED")
    method: Mapped[str] = mapped_column(String, nullable=False) # e.g. CREDIT_CARD, CASH, TRANSFER

    billing_account: Mapped["BillingAccount"] = relationship("BillingAccount", back_populates="payments")
    allocations: Mapped[List["PaymentAllocation"]] = relationship("PaymentAllocation", back_populates="payment")

class PaymentAllocation(TenantMixin, Base):
    __tablename__ = "payment_allocations"

    payment_id: Mapped[UUID] = mapped_column(ForeignKey("payments.id"), nullable=False, index=True)
    invoice_id: Mapped[UUID] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)

    payment: Mapped["Payment"] = relationship("Payment", back_populates="allocations")
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="allocations")
