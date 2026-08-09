from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BillingAccountCreate(BaseModel):
    member_id: UUID | None = None
    user_id: UUID | None = None
    currency: str = "TRY"


class BillingAccountResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    member_id: UUID | None
    user_id: UUID | None
    currency: str
    status: str

    model_config = {"from_attributes": True}


class InvoiceItemCreate(BaseModel):
    description: str
    unit_amount_minor: int = Field(ge=0)
    quantity: int = Field(default=1, ge=1)
    source_type: str | None = None
    source_id: UUID | None = None


class InvoiceCreate(BaseModel):
    billing_account_id: UUID
    items: list[InvoiceItemCreate]
    currency: str = "TRY"
    due_date: datetime | None = None
    membership_id: UUID | None = None
    discount_code: str | None = None
    discount_amount_minor: int | None = Field(default=None, ge=0)
    issue: bool = False


class InvoiceItemResponse(BaseModel):
    id: UUID
    description: str
    unit_amount_minor: int
    quantity: int
    amount_minor: int

    model_config = {"from_attributes": True}


class InvoiceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    billing_account_id: UUID
    membership_id: UUID | None
    invoice_number: str | None
    status: str
    currency: str
    total_amount_minor: int
    paid_amount_minor: int
    discount_amount_minor: int
    remaining_amount_minor: int
    due_date: datetime | None
    issued_at: datetime | None
    items: list[InvoiceItemResponse] = []

    model_config = {"from_attributes": True}


class AllocationCreate(BaseModel):
    invoice_id: UUID
    amount_minor: int = Field(gt=0)


class PaymentCreate(BaseModel):
    billing_account_id: UUID
    amount_minor: int = Field(gt=0)
    method: str
    currency: str = "TRY"
    allocations: list[AllocationCreate] = []
    provider: str | None = None
    provider_ref: str | None = None


class PaymentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    billing_account_id: UUID
    amount_minor: int
    refunded_amount_minor: int
    currency: str
    status: str
    method: str
    provider: str | None
    provider_ref: str | None

    model_config = {"from_attributes": True}


class RefundCreate(BaseModel):
    amount_minor: int = Field(gt=0)
    reason: str | None = None


class RefundResponse(BaseModel):
    id: UUID
    payment_id: UUID
    amount_minor: int
    currency: str
    status: str
    reason: str | None

    model_config = {"from_attributes": True}


class CreditNoteCreate(BaseModel):
    billing_account_id: UUID
    amount_minor: int = Field(gt=0)
    currency: str = "TRY"
    reason: str | None = None


class CreditNoteResponse(BaseModel):
    id: UUID
    billing_account_id: UUID
    amount_minor: int
    remaining_minor: int
    currency: str
    status: str
    reason: str | None

    model_config = {"from_attributes": True}


class CreditApplyRequest(BaseModel):
    invoice_id: UUID
    amount_minor: int = Field(gt=0)


class DiscountCreate(BaseModel):
    code: str
    name: str
    amount_minor: int | None = Field(default=None, ge=0)
    percent_bps: int | None = Field(default=None, ge=0, le=10000)


class DiscountResponse(BaseModel):
    id: UUID
    code: str
    name: str
    amount_minor: int | None
    percent_bps: int | None
    is_active: bool

    model_config = {"from_attributes": True}


class ReconciliationItemCreate(BaseModel):
    external_ref: str
    amount_minor: int
    currency: str = "TRY"


class ReconciliationStart(BaseModel):
    items: list[ReconciliationItemCreate]
    notes: str | None = None


class ReconciliationRunResponse(BaseModel):
    id: UUID
    status: str
    notes: str | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ReconciliationMatchRequest(BaseModel):
    payment_id: UUID
