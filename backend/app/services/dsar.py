"""Member-scoped DSAR export package and erasure with invoice legal holds."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access import AccessAttempt, Checkin
from app.models.booking import (
    ClassBooking,
    ClassBookingStatus,
    PtAppointment,
    PtAppointmentStatus,
)
from app.models.consent import ConsentRecord
from app.models.dsar import (
    KIND_ERASURE,
    KIND_EXPORT,
    STATUS_COMPLETED,
    STATUS_PACKAGED,
    STATUS_RECEIVED,
    STATUS_REJECTED,
    DsarRequest,
)
from app.models.finance import BillingAccount, Invoice, Payment
from app.models.member import Member, Note
from app.models.membership import Membership
from app.models.user import User, UserSession
from app.services.booking import (
    BookingConflict,
    BookingNotFound,
    ClassBookingService,
    PtBookingService,
)
from app.services.storage import get_storage_provider

HOLD_OPEN_INVOICES = "legal_hold_open_invoices"
OPEN_INVOICE_STATUSES = frozenset({"OPEN", "PARTIALLY_PAID", "DRAFT"})


class DsarLegalHold(Exception):
    def __init__(self, reason: str, row: DsarRequest):
        super().__init__(reason)
        self.reason = reason
        self.row = row


DSAR_SLA = timedelta(days=30)
FORBIDDEN_PACKAGE_KEYS = frozenset(
    {
        "one_time_password",
        "invite_token",
        "hashed_password",
        "encrypted_secret",
        "signing_secret",
        "signing_key_material",
        "pan",
        "cvv",
        "card_number",
    }
)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _assert_package_safe(payload: dict) -> None:
    blob = json.dumps(payload, default=str).lower()
    for key in FORBIDDEN_PACKAGE_KEYS:
        if key in blob:
            raise ValueError(f"package_contains_secret:{key}")


class DsarService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = get_storage_provider()

    async def list_for_member(
        self, tenant_id: UUID, member_id: UUID
    ) -> list[DsarRequest]:
        result = await self.db.execute(
            select(DsarRequest)
            .where(
                DsarRequest.tenant_id == tenant_id,
                DsarRequest.member_id == member_id,
            )
            .order_by(DsarRequest.created_at.desc())
            .limit(50)
        )
        return list(result.scalars().all())

    async def list_for_tenant(self, tenant_id: UUID) -> list[DsarRequest]:
        result = await self.db.execute(
            select(DsarRequest)
            .where(DsarRequest.tenant_id == tenant_id)
            .order_by(DsarRequest.created_at.desc())
            .limit(100)
        )
        return list(result.scalars().all())

    async def get(self, tenant_id: UUID, request_id: UUID) -> DsarRequest | None:
        result = await self.db.execute(
            select(DsarRequest).where(
                DsarRequest.tenant_id == tenant_id,
                DsarRequest.id == request_id,
            )
        )
        return result.scalars().first()

    async def request_export(
        self,
        tenant_id: UUID,
        member: Member,
        *,
        requested_by_user_id: UUID | None,
    ) -> tuple[DsarRequest, bool]:
        day = datetime.now(UTC).date().isoformat()
        dedupe = f"dsar-export:{member.id}:{day}"
        existing = (
            await self.db.execute(
                select(DsarRequest).where(
                    DsarRequest.tenant_id == tenant_id,
                    DsarRequest.dedupe_key == dedupe,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing, False

        now = datetime.now(UTC)
        row = DsarRequest(
            id=uuid4(),
            tenant_id=tenant_id,
            member_id=member.id,
            requested_by_user_id=requested_by_user_id,
            kind=KIND_EXPORT,
            status=STATUS_RECEIVED,
            due_at=now + DSAR_SLA,
            dedupe_key=dedupe,
        )
        self.db.add(row)
        await self.db.flush()
        package = await self._build_package(tenant_id, member)
        _assert_package_safe(package)
        raw = json.dumps(package, default=str, ensure_ascii=False).encode("utf-8")
        row.package_uri = await self.storage.save_bytes(tenant_id, row.id, raw)
        row.status = STATUS_PACKAGED
        await self.db.flush()
        return row, True

    async def request_erasure(
        self,
        tenant_id: UUID,
        member: Member,
        *,
        requested_by_user_id: UUID | None,
    ) -> tuple[DsarRequest, bool]:
        """Anonymize PII. Invoices and payments are retained. Open invoices hold."""
        dedupe = f"dsar-erasure:{member.id}"
        existing = (
            await self.db.execute(
                select(DsarRequest).where(
                    DsarRequest.tenant_id == tenant_id,
                    DsarRequest.dedupe_key == dedupe,
                )
            )
        ).scalar_one_or_none()
        if existing is not None and existing.status == STATUS_COMPLETED:
            return existing, False

        now = datetime.now(UTC)
        row = existing
        if row is None:
            row = DsarRequest(
                id=uuid4(),
                tenant_id=tenant_id,
                member_id=member.id,
                requested_by_user_id=requested_by_user_id,
                kind=KIND_ERASURE,
                status=STATUS_RECEIVED,
                due_at=now + DSAR_SLA,
                dedupe_key=dedupe,
            )
            self.db.add(row)
            await self.db.flush()
        else:
            row.requested_by_user_id = requested_by_user_id
            row.status = STATUS_RECEIVED
            row.rejection_reason = None
            row.due_at = now + DSAR_SLA

        hold = await self._open_invoice_hold(tenant_id, member.id)
        if hold:
            row.status = STATUS_REJECTED
            row.rejection_reason = HOLD_OPEN_INVOICES
            await self.db.flush()
            raise DsarLegalHold(HOLD_OPEN_INVOICES, row)

        await self._anonymize_member(tenant_id, member, now)
        row.status = STATUS_COMPLETED
        row.rejection_reason = None
        await self.db.flush()
        return row, True

    async def _open_invoice_hold(self, tenant_id: UUID, member_id: UUID) -> bool:
        invoices = list(
            (
                await self.db.execute(
                    select(Invoice)
                    .join(
                        BillingAccount, Invoice.billing_account_id == BillingAccount.id
                    )
                    .where(
                        Invoice.tenant_id == tenant_id,
                        BillingAccount.member_id == member_id,
                        Invoice.status.in_(OPEN_INVOICE_STATUSES),
                    )
                )
            )
            .scalars()
            .all()
        )
        return len(invoices) > 0

    async def _anonymize_member(
        self, tenant_id: UUID, member: Member, now: datetime
    ) -> None:
        bookings = list(
            (
                await self.db.execute(
                    select(ClassBooking).where(
                        ClassBooking.tenant_id == tenant_id,
                        ClassBooking.member_id == member.id,
                        ClassBooking.status.in_(
                            [
                                ClassBookingStatus.CONFIRMED,
                                ClassBookingStatus.WAITLISTED,
                            ]
                        ),
                    )
                )
            )
            .scalars()
            .all()
        )
        for booking in bookings:
            try:
                await ClassBookingService.cancel_booking(
                    self.db,
                    tenant_id,
                    booking.id,
                    member_id=member.id,
                    reason="dsar_erasure",
                    is_staff=True,
                )
            except (BookingNotFound, BookingConflict):
                continue

        pts = list(
            (
                await self.db.execute(
                    select(PtAppointment).where(
                        PtAppointment.tenant_id == tenant_id,
                        PtAppointment.member_id == member.id,
                        PtAppointment.status == PtAppointmentStatus.CONFIRMED,
                    )
                )
            )
            .scalars()
            .all()
        )
        for appt in pts:
            try:
                await PtBookingService.cancel_appointment(
                    self.db,
                    tenant_id,
                    appt.id,
                    member_id=member.id,
                    is_staff=True,
                )
            except (BookingNotFound, BookingConflict):
                continue

        memberships = list(
            (
                await self.db.execute(
                    select(Membership).where(
                        Membership.tenant_id == tenant_id,
                        Membership.member_id == member.id,
                        Membership.status == "ACTIVE",
                    )
                )
            )
            .scalars()
            .all()
        )
        for membership in memberships:
            membership.status = "CANCELLED"
            membership.end_date = now

        consents = list(
            (
                await self.db.execute(
                    select(ConsentRecord).where(
                        ConsentRecord.tenant_id == tenant_id,
                        ConsentRecord.member_id == member.id,
                        ConsentRecord.status == "GIVEN",
                    )
                )
            )
            .scalars()
            .all()
        )
        for consent in consents:
            consent.status = "WITHDRAWN"
            consent.withdrawn_at = now

        notes = list(
            (
                await self.db.execute(
                    select(Note).where(
                        Note.tenant_id == tenant_id,
                        Note.member_id == member.id,
                    )
                )
            )
            .scalars()
            .all()
        )
        for note in notes:
            note.content = "[anonymized]"

        bound_user_id = member.user_id
        member.first_name = "ANON"
        member.last_name = member.member_number
        member.email = None
        member.phone = None
        member.status = "ANONYMIZED"
        member.user_id = None

        if bound_user_id is not None:
            user = await self.db.get(User, bound_user_id)
            if user is not None:
                user.is_active = False
            sessions = list(
                (
                    await self.db.execute(
                        select(UserSession).where(
                            UserSession.user_id == bound_user_id,
                            UserSession.is_revoked.is_(False),
                        )
                    )
                )
                .scalars()
                .all()
            )
            for session in sessions:
                session.is_revoked = True

    async def download_url(self, tenant_id: UUID, row: DsarRequest) -> str | None:
        if row.status != STATUS_PACKAGED or not row.package_uri:
            return None
        from app.core.config import settings

        return await self.storage.generate_download_url(
            tenant_id,
            row.package_uri,
            settings.REPORT_DOWNLOAD_URL_TTL_SECONDS,
        )

    async def _build_package(self, tenant_id: UUID, member: Member) -> dict:
        memberships = list(
            (
                await self.db.execute(
                    select(Membership).where(
                        Membership.tenant_id == tenant_id,
                        Membership.member_id == member.id,
                    )
                )
            )
            .scalars()
            .all()
        )
        consents = list(
            (
                await self.db.execute(
                    select(ConsentRecord)
                    .where(
                        ConsentRecord.tenant_id == tenant_id,
                        ConsentRecord.member_id == member.id,
                    )
                    .order_by(ConsentRecord.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        checkins = list(
            (
                await self.db.execute(
                    select(Checkin)
                    .where(
                        Checkin.tenant_id == tenant_id,
                        Checkin.member_id == member.id,
                    )
                    .order_by(Checkin.checkin_time.desc())
                    .limit(50)
                )
            )
            .scalars()
            .all()
        )
        attempts = list(
            (
                await self.db.execute(
                    select(AccessAttempt)
                    .where(
                        AccessAttempt.tenant_id == tenant_id,
                        AccessAttempt.member_id == member.id,
                    )
                    .order_by(AccessAttempt.timestamp.desc())
                    .limit(50)
                )
            )
            .scalars()
            .all()
        )
        invoices = list(
            (
                await self.db.execute(
                    select(Invoice)
                    .join(
                        BillingAccount, Invoice.billing_account_id == BillingAccount.id
                    )
                    .where(
                        Invoice.tenant_id == tenant_id,
                        BillingAccount.member_id == member.id,
                    )
                )
            )
            .scalars()
            .all()
        )
        payments = list(
            (
                await self.db.execute(
                    select(Payment)
                    .join(
                        BillingAccount, Payment.billing_account_id == BillingAccount.id
                    )
                    .where(
                        Payment.tenant_id == tenant_id,
                        BillingAccount.member_id == member.id,
                    )
                )
            )
            .scalars()
            .all()
        )
        bookings = list(
            (
                await self.db.execute(
                    select(ClassBooking).where(
                        ClassBooking.tenant_id == tenant_id,
                        ClassBooking.member_id == member.id,
                    )
                )
            )
            .scalars()
            .all()
        )
        pts = list(
            (
                await self.db.execute(
                    select(PtAppointment).where(
                        PtAppointment.tenant_id == tenant_id,
                        PtAppointment.member_id == member.id,
                    )
                )
            )
            .scalars()
            .all()
        )
        return {
            "schema": "gymclubnex.dsar.export.v1",
            "exported_at": _iso(datetime.now(UTC)),
            "member": {
                "id": str(member.id),
                "member_number": member.member_number,
                "first_name": member.first_name,
                "last_name": member.last_name,
                "email": member.email,
                "phone": member.phone,
                "status": member.status,
            },
            "consents": [
                {
                    "consent_type": c.consent_type,
                    "status": c.status,
                    "document_version": c.document_version,
                    "given_at": _iso(c.given_at),
                    "withdrawn_at": _iso(c.withdrawn_at),
                }
                for c in consents
            ],
            "memberships": [
                {
                    "id": str(m.id),
                    "status": m.status,
                    "start_date": _iso(m.start_date),
                    "end_date": _iso(m.end_date),
                }
                for m in memberships
            ],
            "invoices": [
                {
                    "id": str(i.id),
                    "status": i.status,
                    "total_amount_minor": i.total_amount_minor,
                    "paid_amount_minor": i.paid_amount_minor,
                    "currency": i.currency,
                }
                for i in invoices
            ],
            "payments": [
                {
                    "id": str(p.id),
                    "status": p.status,
                    "amount_minor": p.amount_minor,
                    "currency": p.currency,
                }
                for p in payments
            ],
            "checkins": [
                {
                    "id": str(c.id),
                    "checkin_time": _iso(c.checkin_time),
                    "checkout_time": _iso(c.checkout_time),
                }
                for c in checkins
            ],
            "access_attempts": [
                {
                    "id": str(a.id),
                    "status": str(a.status),
                    "denial_reason": a.denial_reason,
                    "timestamp": _iso(a.timestamp),
                }
                for a in attempts
            ],
            "class_bookings": [
                {"id": str(b.id), "status": str(b.status)} for b in bookings
            ],
            "pt_appointments": [
                {"id": str(p.id), "status": str(p.status)} for p in pts
            ],
        }
