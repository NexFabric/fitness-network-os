from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService, SecurityException
from app.models.user import User
from app.schemas.finance import (
    BillingAccountCreate,
    BillingAccountResponse,
    CreditApplyRequest,
    CreditNoteCreate,
    CreditNoteResponse,
    DiscountCreate,
    DiscountResponse,
    InvoiceCreate,
    InvoiceResponse,
    PaymentCreate,
    PaymentResponse,
    ReconciliationMatchRequest,
    ReconciliationRunResponse,
    ReconciliationStart,
    RefundCreate,
    RefundResponse,
)
from app.services.finance import FinanceService

router = APIRouter()


def _require(user: User, tenant_id: UUID, permission: str) -> None:
    if not AuthorizationService.is_authorized(
        user=user, permission=permission, resource_tenant_id=tenant_id
    ):
        raise SecurityException()


def _invoice_response(inv) -> InvoiceResponse:
    return InvoiceResponse(
        id=inv.id,
        tenant_id=inv.tenant_id,
        billing_account_id=inv.billing_account_id,
        membership_id=inv.membership_id,
        invoice_number=inv.invoice_number,
        status=inv.status,
        currency=inv.currency,
        total_amount_minor=inv.total_amount_minor,
        paid_amount_minor=inv.paid_amount_minor,
        discount_amount_minor=inv.discount_amount_minor,
        remaining_amount_minor=inv.total_amount_minor - inv.paid_amount_minor,
        due_date=inv.due_date,
        issued_at=inv.issued_at,
        items=list(inv.items) if inv.items is not None else [],
    )


@router.post("/billing-accounts", response_model=BillingAccountResponse)
async def create_billing_account(
    body: BillingAccountCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "finance:write")
    svc = FinanceService(db)
    try:
        account = await svc.get_or_create_billing_account(
            tenant_id,
            member_id=body.member_id,
            user_id=body.user_id,
            currency=body.currency,
        )
        await db.commit()
        await db.refresh(account)
        return account
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(
    body: InvoiceCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    _require(current_user, tenant_id, "finance:write")
    svc = FinanceService(db)
    try:
        inv = await svc.create_invoice(
            tenant_id,
            body.billing_account_id,
            [item.model_dump() for item in body.items],
            currency=body.currency,
            due_date=body.due_date,
            membership_id=body.membership_id,
            discount_code=body.discount_code,
            discount_amount_minor=body.discount_amount_minor,
            idempotency_key=idempotency_key,
            issue=body.issue,
        )
        await db.commit()
        await db.refresh(inv, attribute_names=["items"])
        return _invoice_response(inv)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/invoices/{invoice_id}/issue", response_model=InvoiceResponse)
async def issue_invoice(
    invoice_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "finance:write")
    svc = FinanceService(db)
    try:
        inv = await svc.issue_invoice(tenant_id, invoice_id)
        await db.commit()
        await db.refresh(inv, attribute_names=["items"])
        return _invoice_response(inv)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/invoices/{invoice_id}/void", response_model=InvoiceResponse)
async def void_invoice(
    invoice_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "finance:write")
    svc = FinanceService(db)
    try:
        inv = await svc.void_invoice(tenant_id, invoice_id)
        await db.commit()
        await db.refresh(inv, attribute_names=["items"])
        return _invoice_response(inv)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/payments", response_model=PaymentResponse)
async def create_payment(
    body: PaymentCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    _require(current_user, tenant_id, "finance:write")
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required for payments.",
        )
    svc = FinanceService(db)
    try:
        payment = await svc.record_payment(
            tenant_id,
            body.billing_account_id,
            body.amount_minor,
            body.method,
            currency=body.currency,
            allocations=[a.model_dump() for a in body.allocations],
            provider=body.provider,
            provider_ref=body.provider_ref,
            idempotency_key=idempotency_key,
        )
        await db.commit()
        await db.refresh(payment)
        return payment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/payments/{payment_id}/refunds", response_model=RefundResponse)
async def refund_payment(
    payment_id: UUID,
    body: RefundCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    _require(current_user, tenant_id, "finance:refund")
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required for refunds.",
        )
    svc = FinanceService(db)
    try:
        refund = await svc.refund_payment(
            tenant_id,
            payment_id,
            body.amount_minor,
            idempotency_key,
            reason=body.reason,
            actor_id=current_user.id,
        )
        await db.commit()
        await db.refresh(refund)
        return refund
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/credits", response_model=CreditNoteResponse)
async def issue_credit(
    body: CreditNoteCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    _require(current_user, tenant_id, "finance:credit")
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required for credits.",
        )
    svc = FinanceService(db)
    try:
        note = await svc.issue_credit(
            tenant_id,
            body.billing_account_id,
            body.amount_minor,
            idempotency_key,
            currency=body.currency,
            reason=body.reason,
            actor_id=current_user.id,
        )
        await db.commit()
        await db.refresh(note)
        return note
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/credits/{credit_id}/apply")
async def apply_credit(
    credit_id: UUID,
    body: CreditApplyRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "finance:credit")
    svc = FinanceService(db)
    try:
        app = await svc.apply_credit_to_invoice(
            tenant_id, credit_id, body.invoice_id, body.amount_minor
        )
        await db.commit()
        return {
            "id": str(app.id),
            "credit_note_id": str(app.credit_note_id),
            "invoice_id": str(app.invoice_id),
            "amount_minor": app.amount_minor,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/discounts", response_model=DiscountResponse)
async def create_discount(
    body: DiscountCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "finance:manage")
    svc = FinanceService(db)
    try:
        disc = await svc.create_discount(
            tenant_id,
            body.code,
            body.name,
            amount_minor=body.amount_minor,
            percent_bps=body.percent_bps,
        )
        await db.commit()
        await db.refresh(disc)
        return disc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/reconciliations", response_model=ReconciliationRunResponse)
async def start_reconciliation(
    body: ReconciliationStart,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "finance:reconcile")
    svc = FinanceService(db)
    try:
        run = await svc.start_reconciliation(
            tenant_id,
            [i.model_dump() for i in body.items],
            notes=body.notes,
            actor_id=current_user.id,
        )
        await db.commit()
        await db.refresh(run)
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/reconciliations/items/{item_id}/match")
async def match_reconciliation_item(
    item_id: UUID,
    body: ReconciliationMatchRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "finance:reconcile")
    svc = FinanceService(db)
    try:
        item = await svc.match_reconciliation_item(
            tenant_id, item_id, body.payment_id
        )
        await db.commit()
        return {
            "id": str(item.id),
            "status": item.status,
            "matched_payment_id": str(item.matched_payment_id)
            if item.matched_payment_id
            else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post(
    "/reconciliations/{run_id}/complete", response_model=ReconciliationRunResponse
)
async def complete_reconciliation(
    run_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "finance:reconcile")
    svc = FinanceService(db)
    try:
        run = await svc.complete_reconciliation(tenant_id, run_id)
        await db.commit()
        await db.refresh(run)
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
