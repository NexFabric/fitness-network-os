"""Finance domain service — amount_minor only, immutable status transitions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.money import assert_amount_minor, assert_quantity
from app.models.finance import (
    BillingAccount,
    CreditApplication,
    CreditNote,
    CreditNoteStatus,
    Discount,
    DunningPolicy,
    Invoice,
    InvoiceDiscount,
    InvoiceItem,
    InvoiceStatus,
    Payment,
    PaymentAllocation,
    PaymentAllocationReversal,
    PaymentAttempt,
    PaymentAttemptStatus,
    PaymentStatus,
    ReconciliationItem,
    ReconciliationItemStatus,
    ReconciliationRun,
    ReconciliationStatus,
    Refund,
    RefundStatus,
)
from app.models.member import Member


class FinanceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------
    # Billing accounts
    # ------------------------------------------------------------------

    async def get_or_create_billing_account(
        self,
        tenant_id: UUID,
        *,
        member_id: UUID | None = None,
        user_id: UUID | None = None,
        currency: str = "TRY",
    ) -> BillingAccount:
        if member_id is None and user_id is None:
            raise ValueError("member_id or user_id required")

        if member_id is not None:
            member = (
                await self.session.execute(
                    select(Member).where(
                        Member.tenant_id == tenant_id, Member.id == member_id
                    )
                )
            ).scalar_one_or_none()
            if not member:
                raise ValueError("Member not found")

            existing = (
                await self.session.execute(
                    select(BillingAccount).where(
                        BillingAccount.tenant_id == tenant_id,
                        BillingAccount.member_id == member_id,
                    )
                )
            ).scalar_one_or_none()
            if existing:
                return existing

        account = BillingAccount(
            tenant_id=tenant_id,
            member_id=member_id,
            user_id=user_id,
            currency=currency.upper(),
            status="ACTIVE",
        )
        self.session.add(account)
        await self.session.flush()
        return account

    # ------------------------------------------------------------------
    # Invoices
    # ------------------------------------------------------------------

    async def create_invoice(
        self,
        tenant_id: UUID,
        billing_account_id: UUID,
        items: list[dict],
        *,
        currency: str = "TRY",
        due_date: datetime | None = None,
        membership_id: UUID | None = None,
        discount_code: str | None = None,
        discount_amount_minor: int | None = None,
        idempotency_key: str | None = None,
        issue: bool = False,
    ) -> Invoice:
        if idempotency_key:
            existing = (
                await self.session.execute(
                    select(Invoice).where(
                        Invoice.tenant_id == tenant_id,
                        Invoice.idempotency_key == idempotency_key,
                    )
                )
            ).scalar_one_or_none()
            if existing:
                return existing

        account = await self._get_billing_account(
            tenant_id, billing_account_id, for_update=True
        )
        if not items:
            raise ValueError("Invoice requires at least one item")

        line_total = 0
        built_items: list[InvoiceItem] = []
        for raw in items:
            qty = assert_quantity(raw.get("quantity", 1))
            unit_raw = (
                raw["unit_amount_minor"]
                if "unit_amount_minor" in raw
                else raw["amount_minor"]
            )
            unit = assert_amount_minor(unit_raw)
            if unit < 0:
                raise ValueError("unit_amount_minor must be >= 0")
            amount = unit * qty
            if amount < 0:
                raise ValueError("line amount cannot be negative")
            line_total += amount
            built_items.append(
                InvoiceItem(
                    tenant_id=tenant_id,
                    description=str(raw["description"]),
                    unit_amount_minor=unit,
                    quantity=qty,
                    amount_minor=amount,
                    source_type=raw.get("source_type"),
                    source_id=raw.get("source_id"),
                )
            )

        discount_total = 0
        inv_discounts: list[InvoiceDiscount] = []
        if discount_code:
            disc = (
                await self.session.execute(
                    select(Discount).where(
                        Discount.tenant_id == tenant_id,
                        Discount.code == discount_code,
                        Discount.is_active.is_(True),
                    )
                )
            ).scalar_one_or_none()
            if not disc:
                raise ValueError("Discount not found or inactive")
            discount_total = self._compute_discount(disc, line_total)
            inv_discounts.append(
                InvoiceDiscount(
                    tenant_id=tenant_id,
                    discount_id=disc.id,
                    description=f"Discount {disc.code}",
                    amount_minor=discount_total,
                )
            )
        elif discount_amount_minor is not None:
            if discount_amount_minor < 0:
                raise ValueError("discount_amount_minor must be >= 0")
            if discount_amount_minor > line_total:
                raise ValueError("discount cannot exceed line total")
            discount_total = discount_amount_minor
            if discount_total > 0:
                inv_discounts.append(
                    InvoiceDiscount(
                        tenant_id=tenant_id,
                        discount_id=None,
                        description="Manual discount",
                        amount_minor=discount_total,
                    )
                )

        total = line_total - discount_total
        if total < 0:
            raise ValueError("Invoice total cannot be negative")

        status = InvoiceStatus.DRAFT.value
        issued_at = None
        invoice_number = None
        if issue:
            status = InvoiceStatus.OPEN.value if total > 0 else InvoiceStatus.PAID.value
            issued_at = datetime.now(UTC)
            invoice_number = self._generate_invoice_number()

        invoice = Invoice(
            tenant_id=tenant_id,
            billing_account_id=account.id,
            membership_id=membership_id,
            invoice_number=invoice_number,
            status=status,
            due_date=due_date,
            issued_at=issued_at,
            currency=currency.upper(),
            total_amount_minor=total,
            paid_amount_minor=0,
            discount_amount_minor=discount_total,
            idempotency_key=idempotency_key,
        )
        self.session.add(invoice)
        await self.session.flush()

        for item in built_items:
            item.invoice_id = invoice.id
            self.session.add(item)
        for d in inv_discounts:
            d.invoice_id = invoice.id
            self.session.add(d)

        await self.session.flush()
        return invoice

    async def issue_invoice(self, tenant_id: UUID, invoice_id: UUID) -> Invoice:
        invoice = await self._get_invoice(tenant_id, invoice_id, for_update=True)
        if invoice.status != InvoiceStatus.DRAFT.value:
            raise ValueError(f"Cannot issue invoice in status {invoice.status}")
        invoice.status = (
            InvoiceStatus.OPEN.value
            if invoice.total_amount_minor > 0
            else InvoiceStatus.PAID.value
        )
        invoice.issued_at = datetime.now(UTC)
        if not invoice.invoice_number:
            invoice.invoice_number = self._generate_invoice_number()
        await self.session.flush()
        return invoice

    async def void_invoice(
        self, tenant_id: UUID, invoice_id: UUID, *, reason: str | None = None
    ) -> Invoice:
        invoice = await self._get_invoice(tenant_id, invoice_id, for_update=True)
        if invoice.status in (InvoiceStatus.PAID.value, InvoiceStatus.VOID.value):
            raise ValueError(f"Cannot void invoice in status {invoice.status}")
        if invoice.paid_amount_minor > 0:
            raise ValueError("Cannot void invoice with payments; refund first")
        invoice.status = InvoiceStatus.VOID.value
        invoice.voided_at = datetime.now(UTC)
        await self.session.flush()
        return invoice

    # ------------------------------------------------------------------
    # Payments & allocations
    # ------------------------------------------------------------------

    async def record_payment(
        self,
        tenant_id: UUID,
        billing_account_id: UUID,
        amount_minor: int,
        method: str,
        *,
        currency: str = "TRY",
        allocations: list[dict] | None = None,
        provider: str | None = None,
        provider_ref: str | None = None,
        idempotency_key: str | None = None,
    ) -> Payment:
        amount_minor = assert_amount_minor(amount_minor)
        if amount_minor <= 0:
            raise ValueError("amount_minor must be > 0")

        if idempotency_key:
            existing = (
                await self.session.execute(
                    select(Payment).where(
                        Payment.tenant_id == tenant_id,
                        Payment.idempotency_key == idempotency_key,
                    )
                )
            ).scalar_one_or_none()
            if existing:
                return existing

        account = await self._get_billing_account(
            tenant_id, billing_account_id, for_update=True
        )
        if account.currency.upper() != currency.upper():
            raise ValueError("Payment currency must match billing account currency")

        payment = Payment(
            tenant_id=tenant_id,
            billing_account_id=account.id,
            amount_minor=amount_minor,
            refunded_amount_minor=0,
            currency=currency.upper(),
            status=PaymentStatus.SUCCEEDED.value,
            method=method,
            provider=provider,
            provider_ref=provider_ref,
            idempotency_key=idempotency_key,
            paid_at=datetime.now(UTC),
        )
        self.session.add(payment)
        await self.session.flush()

        if allocations:
            await self._apply_allocations(
                tenant_id, payment, allocations, billing_account_id=account.id
            )

        await self.session.flush()
        return payment

    async def allocate_payment(
        self,
        tenant_id: UUID,
        payment_id: UUID,
        allocations: list[dict],
    ) -> Payment:
        payment = await self._get_payment(tenant_id, payment_id, for_update=True)
        if payment.status not in (
            PaymentStatus.SUCCEEDED.value,
            PaymentStatus.PARTIALLY_REFUNDED.value,
        ):
            raise ValueError(f"Cannot allocate payment in status {payment.status}")
        await self._apply_allocations(
            tenant_id,
            payment,
            allocations,
            billing_account_id=payment.billing_account_id,
        )
        await self.session.flush()
        return payment

    async def _apply_allocations(
        self,
        tenant_id: UUID,
        payment: Payment,
        allocations: list[dict],
        *,
        billing_account_id: UUID,
    ) -> None:
        already = await self._payment_allocated_total(tenant_id, payment.id)
        available = payment.amount_minor - payment.refunded_amount_minor - already
        if available < 0:
            raise ValueError("Payment over-allocated")

        for alloc in allocations:
            invoice_id = alloc["invoice_id"]
            amount = assert_amount_minor(alloc["amount_minor"])
            if amount <= 0:
                raise ValueError("allocation amount_minor must be > 0")
            if amount > available:
                raise ValueError("allocation exceeds payment available amount")

            invoice = await self._get_invoice(tenant_id, invoice_id, for_update=True)
            if invoice.billing_account_id != billing_account_id:
                raise ValueError("Invoice and payment billing accounts differ")
            if invoice.currency.upper() != payment.currency.upper():
                raise ValueError("Invoice and payment currency mismatch")
            if invoice.status not in (
                InvoiceStatus.OPEN.value,
                InvoiceStatus.PARTIALLY_PAID.value,
            ):
                raise ValueError(
                    f"Cannot allocate to invoice in status {invoice.status}"
                )

            remaining = invoice.total_amount_minor - invoice.paid_amount_minor
            if amount > remaining:
                raise ValueError("allocation exceeds invoice remaining balance")

            self.session.add(
                PaymentAllocation(
                    tenant_id=tenant_id,
                    payment_id=payment.id,
                    invoice_id=invoice.id,
                    amount_minor=amount,
                )
            )
            invoice.paid_amount_minor += amount
            invoice.status = self._invoice_status_from_paid(invoice)
            available -= amount

    # ------------------------------------------------------------------
    # Refunds
    # ------------------------------------------------------------------

    async def refund_payment(
        self,
        tenant_id: UUID,
        payment_id: UUID,
        amount_minor: int,
        idempotency_key: str,
        *,
        reason: str | None = None,
        actor_id: UUID | None = None,
    ) -> Refund:
        amount_minor = assert_amount_minor(amount_minor)
        if amount_minor <= 0:
            raise ValueError("refund amount_minor must be > 0")

        existing = (
            await self.session.execute(
                select(Refund).where(
                    Refund.tenant_id == tenant_id,
                    Refund.idempotency_key == idempotency_key,
                )
            )
        ).scalar_one_or_none()
        if existing:
            return existing

        payment = await self._get_payment(tenant_id, payment_id, for_update=True)
        if payment.status not in (
            PaymentStatus.SUCCEEDED.value,
            PaymentStatus.PARTIALLY_REFUNDED.value,
        ):
            raise ValueError(f"Cannot refund payment in status {payment.status}")

        refundable = payment.amount_minor - payment.refunded_amount_minor
        if amount_minor > refundable:
            raise ValueError("refund exceeds refundable amount")

        refund = Refund(
            tenant_id=tenant_id,
            payment_id=payment.id,
            amount_minor=amount_minor,
            currency=payment.currency,
            status=RefundStatus.SUCCEEDED.value,
            reason=reason,
            idempotency_key=idempotency_key,
            actor_id=actor_id,
        )
        self.session.add(refund)
        await self.session.flush()

        # Append-only allocation reversals (never mutate/delete allocation rows)
        await self._unwind_allocations_for_refund(
            tenant_id, payment, amount_minor, refund_id=refund.id
        )

        payment.refunded_amount_minor += amount_minor
        if payment.refunded_amount_minor >= payment.amount_minor:
            payment.status = PaymentStatus.REFUNDED.value
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED.value

        await self.session.flush()
        return refund

    async def _allocation_remaining(
        self, tenant_id: UUID, allocation: PaymentAllocation
    ) -> int:
        rev = (
            (
                await self.session.execute(
                    select(PaymentAllocationReversal.amount_minor).where(
                        PaymentAllocationReversal.tenant_id == tenant_id,
                        PaymentAllocationReversal.allocation_id == allocation.id,
                    )
                )
            )
            .scalars()
            .all()
        )
        return allocation.amount_minor - sum(rev)

    async def _unwind_allocations_for_refund(
        self,
        tenant_id: UUID,
        payment: Payment,
        refund_amount: int,
        *,
        refund_id: UUID | None = None,
    ) -> None:
        """LIFO reverse allocations via append-only PaymentAllocationReversal rows."""
        allocs = (
            (
                await self.session.execute(
                    select(PaymentAllocation)
                    .where(
                        PaymentAllocation.tenant_id == tenant_id,
                        PaymentAllocation.payment_id == payment.id,
                    )
                    .order_by(PaymentAllocation.created_at.desc())
                    .with_for_update()
                )
            )
            .scalars()
            .all()
        )

        remaining_refund = refund_amount
        for alloc in allocs:
            if remaining_refund <= 0:
                break
            open_amt = await self._allocation_remaining(tenant_id, alloc)
            if open_amt <= 0:
                continue
            invoice = await self._get_invoice(
                tenant_id, alloc.invoice_id, for_update=True
            )
            reduce_by = min(open_amt, remaining_refund)
            self.session.add(
                PaymentAllocationReversal(
                    tenant_id=tenant_id,
                    allocation_id=alloc.id,
                    refund_id=refund_id,
                    amount_minor=reduce_by,
                    reason="refund_unwind",
                )
            )
            invoice.paid_amount_minor -= reduce_by
            if invoice.paid_amount_minor < 0:
                raise ValueError("invoice paid amount invariant broken")
            invoice.status = self._invoice_status_from_paid(invoice)
            remaining_refund -= reduce_by

        # Unallocated payment headroom does not require invoice unwind
        # remaining_refund can stay > 0 if payment was only partially allocated

    # ------------------------------------------------------------------
    # Credits
    # ------------------------------------------------------------------

    async def issue_credit(
        self,
        tenant_id: UUID,
        billing_account_id: UUID,
        amount_minor: int,
        idempotency_key: str,
        *,
        currency: str = "TRY",
        reason: str | None = None,
        actor_id: UUID | None = None,
    ) -> CreditNote:
        amount_minor = assert_amount_minor(amount_minor)
        if amount_minor <= 0:
            raise ValueError("credit amount_minor must be > 0")

        existing = (
            await self.session.execute(
                select(CreditNote).where(
                    CreditNote.tenant_id == tenant_id,
                    CreditNote.idempotency_key == idempotency_key,
                )
            )
        ).scalar_one_or_none()
        if existing:
            return existing

        account = await self._get_billing_account(
            tenant_id, billing_account_id, for_update=True
        )
        if account.currency.upper() != currency.upper():
            raise ValueError("Credit currency must match billing account")

        note = CreditNote(
            tenant_id=tenant_id,
            billing_account_id=account.id,
            amount_minor=amount_minor,
            remaining_minor=amount_minor,
            currency=currency.upper(),
            status=CreditNoteStatus.OPEN.value,
            reason=reason,
            idempotency_key=idempotency_key,
            actor_id=actor_id,
        )
        self.session.add(note)
        await self.session.flush()
        return note

    async def apply_credit_to_invoice(
        self,
        tenant_id: UUID,
        credit_note_id: UUID,
        invoice_id: UUID,
        amount_minor: int,
    ) -> CreditApplication:
        amount_minor = assert_amount_minor(amount_minor)
        if amount_minor <= 0:
            raise ValueError("amount_minor must be > 0")

        credit = (
            await self.session.execute(
                select(CreditNote)
                .where(
                    CreditNote.tenant_id == tenant_id,
                    CreditNote.id == credit_note_id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if not credit:
            raise ValueError("Credit note not found")
        if credit.status != CreditNoteStatus.OPEN.value:
            raise ValueError(f"Cannot apply credit in status {credit.status}")
        if amount_minor > credit.remaining_minor:
            raise ValueError("amount exceeds credit remaining")

        invoice = await self._get_invoice(tenant_id, invoice_id, for_update=True)
        if invoice.billing_account_id != credit.billing_account_id:
            raise ValueError("Credit and invoice billing accounts differ")
        if invoice.status not in (
            InvoiceStatus.OPEN.value,
            InvoiceStatus.PARTIALLY_PAID.value,
        ):
            raise ValueError(
                f"Cannot apply credit to invoice in status {invoice.status}"
            )

        remaining = invoice.total_amount_minor - invoice.paid_amount_minor
        if amount_minor > remaining:
            raise ValueError("credit application exceeds invoice remaining")

        credit.remaining_minor -= amount_minor
        if credit.remaining_minor == 0:
            credit.status = CreditNoteStatus.FULLY_APPLIED.value

        invoice.paid_amount_minor += amount_minor
        invoice.status = self._invoice_status_from_paid(invoice)

        app = CreditApplication(
            tenant_id=tenant_id,
            credit_note_id=credit.id,
            invoice_id=invoice.id,
            amount_minor=amount_minor,
        )
        self.session.add(app)
        await self.session.flush()
        return app

    # ------------------------------------------------------------------
    # Discounts catalog
    # ------------------------------------------------------------------

    async def create_discount(
        self,
        tenant_id: UUID,
        code: str,
        name: str,
        *,
        amount_minor: int | None = None,
        percent_bps: int | None = None,
    ) -> Discount:
        if (amount_minor is None) == (percent_bps is None):
            raise ValueError("Provide exactly one of amount_minor or percent_bps")
        if amount_minor is not None and amount_minor < 0:
            raise ValueError("amount_minor must be >= 0")
        if percent_bps is not None and not (0 <= percent_bps <= 10000):
            raise ValueError("percent_bps must be 0..10000")

        disc = Discount(
            tenant_id=tenant_id,
            code=code,
            name=name,
            amount_minor=amount_minor,
            percent_bps=percent_bps,
            is_active=True,
        )
        self.session.add(disc)
        try:
            await self.session.flush()
        except IntegrityError as e:
            raise ValueError("Discount code already exists") from e
        return disc

    # ------------------------------------------------------------------
    # Reconciliation
    # ------------------------------------------------------------------

    async def start_reconciliation(
        self,
        tenant_id: UUID,
        items: list[dict],
        *,
        notes: str | None = None,
        actor_id: UUID | None = None,
    ) -> ReconciliationRun:
        if not items:
            raise ValueError("reconciliation requires items")

        run = ReconciliationRun(
            tenant_id=tenant_id,
            status=ReconciliationStatus.OPEN.value,
            notes=notes,
            started_at=datetime.now(UTC),
            actor_id=actor_id,
        )
        self.session.add(run)
        await self.session.flush()

        for raw in items:
            amount = assert_amount_minor(raw["amount_minor"])
            if amount == 0:
                raise ValueError("reconciliation item amount cannot be 0")
            item = ReconciliationItem(
                tenant_id=tenant_id,
                run_id=run.id,
                external_ref=str(raw["external_ref"]),
                amount_minor=amount,
                currency=str(raw.get("currency", "TRY")).upper(),
                status=ReconciliationItemStatus.UNMATCHED.value,
            )
            self.session.add(item)

        await self.session.flush()
        return run

    async def match_reconciliation_item(
        self,
        tenant_id: UUID,
        item_id: UUID,
        payment_id: UUID,
    ) -> ReconciliationItem:
        item = (
            await self.session.execute(
                select(ReconciliationItem)
                .where(
                    ReconciliationItem.tenant_id == tenant_id,
                    ReconciliationItem.id == item_id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if not item:
            raise ValueError("Reconciliation item not found")
        if item.status != ReconciliationItemStatus.UNMATCHED.value:
            raise ValueError(f"Item already {item.status}")

        payment = await self._get_payment(tenant_id, payment_id, for_update=True)
        if payment.amount_minor != abs(item.amount_minor):
            raise ValueError("Payment amount does not match reconciliation item")
        if payment.currency.upper() != item.currency.upper():
            raise ValueError("Currency mismatch")

        # Prevent double-matching: check if payment is already matched elsewhere
        already_matched = (
            await self.session.execute(
                select(ReconciliationItem).where(
                    ReconciliationItem.tenant_id == tenant_id,
                    ReconciliationItem.matched_payment_id == payment.id,
                    ReconciliationItem.status == ReconciliationItemStatus.MATCHED.value,
                    ReconciliationItem.id != item_id,
                )
            )
        ).scalar_one_or_none()
        if already_matched:
            raise ValueError("Payment is already matched to another reconciliation item")

        item.matched_payment_id = payment.id
        item.status = ReconciliationItemStatus.MATCHED.value
        await self.session.flush()
        return item

    async def complete_reconciliation(
        self, tenant_id: UUID, run_id: UUID
    ) -> ReconciliationRun:
        run = (
            await self.session.execute(
                select(ReconciliationRun)
                .where(
                    ReconciliationRun.tenant_id == tenant_id,
                    ReconciliationRun.id == run_id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if not run:
            raise ValueError("Reconciliation run not found")
        if run.status != ReconciliationStatus.OPEN.value:
            raise ValueError(f"Cannot complete run in status {run.status}")
        run.status = ReconciliationStatus.COMPLETED.value
        run.completed_at = datetime.now(UTC)
        await self.session.flush()
        return run

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_invoice_number() -> str:
        return f"INV-{datetime.now(UTC).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"

    @staticmethod
    def _compute_discount(disc: Discount, line_total: int) -> int:
        if disc.amount_minor is not None:
            return min(disc.amount_minor, line_total)
        assert disc.percent_bps is not None
        # integer math: floor(line_total * bps / 10000)
        return min((line_total * disc.percent_bps) // 10000, line_total)

    @staticmethod
    def _invoice_status_from_paid(invoice: Invoice) -> str:
        if invoice.paid_amount_minor <= 0:
            return InvoiceStatus.OPEN.value
        if invoice.paid_amount_minor >= invoice.total_amount_minor:
            return InvoiceStatus.PAID.value
        return InvoiceStatus.PARTIALLY_PAID.value

    async def list_invoices(
        self,
        tenant_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        member_id: UUID | None = None,
    ) -> tuple[list[Invoice], int]:
        from sqlalchemy import func
        from sqlalchemy.orm import selectinload

        stmt = select(Invoice).where(Invoice.tenant_id == tenant_id)
        if member_id:
            stmt = stmt.join(
                BillingAccount, Invoice.billing_account_id == BillingAccount.id
            ).where(BillingAccount.member_id == member_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.options(selectinload(Invoice.items))
            .order_by(Invoice.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = (await self.session.execute(stmt)).scalars().all()
        return list(items), total

    async def list_payments(
        self,
        tenant_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        member_id: UUID | None = None,
    ) -> tuple[list[Payment], int]:
        from sqlalchemy import func

        stmt = select(Payment).where(Payment.tenant_id == tenant_id)
        if member_id:
            stmt = stmt.join(
                BillingAccount, Payment.billing_account_id == BillingAccount.id
            ).where(BillingAccount.member_id == member_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Payment.created_at.desc()).offset(skip).limit(limit)
        items = (await self.session.execute(stmt)).scalars().all()
        return list(items), total

    async def _get_billing_account(
        self, tenant_id: UUID, account_id: UUID, *, for_update: bool = False
    ) -> BillingAccount:
        stmt = select(BillingAccount).where(
            BillingAccount.tenant_id == tenant_id,
            BillingAccount.id == account_id,
        )
        if for_update:
            stmt = stmt.with_for_update()
        account = (await self.session.execute(stmt)).scalar_one_or_none()
        if not account:
            raise ValueError("Billing account not found")
        return account

    async def _get_invoice(
        self, tenant_id: UUID, invoice_id: UUID, *, for_update: bool = False
    ) -> Invoice:
        stmt = select(Invoice).where(
            Invoice.tenant_id == tenant_id, Invoice.id == invoice_id
        )
        if for_update:
            stmt = stmt.with_for_update()
        invoice = (await self.session.execute(stmt)).scalar_one_or_none()
        if not invoice:
            raise ValueError("Invoice not found")
        return invoice

    async def _get_payment(
        self, tenant_id: UUID, payment_id: UUID, *, for_update: bool = False
    ) -> Payment:
        stmt = select(Payment).where(
            Payment.tenant_id == tenant_id, Payment.id == payment_id
        )
        if for_update:
            stmt = stmt.with_for_update()
        payment = (await self.session.execute(stmt)).scalar_one_or_none()
        if not payment:
            raise ValueError("Payment not found")
        return payment

    async def _payment_allocated_total(self, tenant_id: UUID, payment_id: UUID) -> int:
        """Net allocated = sum(allocations) - sum(reversals for those allocations)."""
        allocs = (
            (
                await self.session.execute(
                    select(PaymentAllocation).where(
                        PaymentAllocation.tenant_id == tenant_id,
                        PaymentAllocation.payment_id == payment_id,
                    )
                )
            )
            .scalars()
            .all()
        )
        total = 0
        for alloc in allocs:
            total += await self._allocation_remaining(tenant_id, alloc)
        return total

    def invoice_remaining(self, invoice: Invoice) -> int:
        return invoice.total_amount_minor - invoice.paid_amount_minor

    # ------------------------------------------------------------------
    # Payment attempts & Dunning
    # ------------------------------------------------------------------

    async def get_or_create_dunning_policy(self, tenant_id: UUID) -> DunningPolicy:
        stmt = select(DunningPolicy).where(
            DunningPolicy.tenant_id == tenant_id,
            DunningPolicy.is_active.is_(True),
        )
        policy = (await self.session.execute(stmt)).scalars().first()
        if not policy:
            policy = DunningPolicy(
                tenant_id=tenant_id,
                name="Default Dunning Policy",
                grace_period_days=3,
                max_retry_attempts=3,
                retry_interval_days=2,
                block_access_on_failure=True,
                is_active=True,
            )
            self.session.add(policy)
            await self.session.flush()
        return policy

    async def record_payment_attempt(
        self,
        tenant_id: UUID,
        *,
        invoice_id: UUID,
        amount_minor: int,
        status: PaymentAttemptStatus | str,
        currency: str = "TRY",
        gateway_provider: str | None = None,
        gateway_attempt_ref: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> PaymentAttempt:
        assert_amount_minor(amount_minor)
        invoice = await self._get_invoice(tenant_id, invoice_id, for_update=True)
        status_val = (
            status.value if isinstance(status, PaymentAttemptStatus) else str(status)
        )

        attempt = PaymentAttempt(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            billing_account_id=invoice.billing_account_id,
            attempt_number=invoice.retry_count + 1,
            amount_minor=amount_minor,
            currency=currency,
            status=status_val,
            gateway_provider=gateway_provider,
            gateway_attempt_ref=gateway_attempt_ref,
            error_code=error_code,
            error_message=error_message,
            attempted_at=datetime.now(UTC),
        )
        self.session.add(attempt)
        invoice.retry_count += 1

        if status_val == PaymentAttemptStatus.FAILED.value:
            policy = await self.get_or_create_dunning_policy(tenant_id)
            if invoice.retry_count >= policy.max_retry_attempts:
                invoice.next_retry_at = None
            else:
                invoice.next_retry_at = datetime.now(UTC) + timedelta(
                    days=policy.retry_interval_days
                )
        elif status_val == PaymentAttemptStatus.SUCCEEDED.value:
            invoice.next_retry_at = None

        await self.session.flush()
        return attempt

    async def list_payment_attempts(
        self, tenant_id: UUID, invoice_id: UUID
    ) -> list[PaymentAttempt]:
        stmt = (
            select(PaymentAttempt)
            .where(
                PaymentAttempt.tenant_id == tenant_id,
                PaymentAttempt.invoice_id == invoice_id,
            )
            .order_by(PaymentAttempt.attempt_number.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())
